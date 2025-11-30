import time
import joblib
import json
import pandas as pd
from django.core.management.base import BaseCommand
from algorithms.models import Location, WeatherLog, Prediction
from algorithms.services import fetch_and_map_weather


class Command(BaseCommand):
    help = 'Pobiera dane pogodowe i generuje predykcje ML'

    def handle(self, *args, **kwargs):
        # 1. Ładowanie modelu (najlepiej raz na początku skryptu)
        try:
            self.stdout.write("Ładowanie modelu ML...")
            model_rf = joblib.load("model_rf.pkl")
            self.stdout.write(self.style.SUCCESS("Model załadowany."))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Błąd ładowania modelu: {e}"))
            return

        # Próba załadowania encodera kolumn kategorycznych (zalecane: zapisać encoder podczas treningu)
        cat_encoder = None
        label_encoders = None
        try:
            cat_encoder = joblib.load("cat_encoder.pkl")  # np. ColumnTransformer/OneHotEncoder/LabelEncoder
            self.stdout.write(self.style.SUCCESS("Załadowano cat_encoder.pkl"))
        except Exception:
            try:
                label_encoders = joblib.load("label_encoders.pkl")  # dict kolumna -> sklearn LabelEncoder lub dict mapping
                self.stdout.write(self.style.SUCCESS("Załadowano label_encoders.pkl"))
            except Exception:
                label_encoders = {}
                self.stdout.write(self.style.WARNING(
                    "Nie znaleziono zapisanych encoderów (cat_encoder.pkl / label_encoders.pkl). "
                    "Jeśli to możliwe, zapisz encodery podczas treningu i podaj je tutaj."
                ))

        # 2. Definicja kolumn wejściowych (kolejność musi być identyczna jak przy treningu!)
        feature_columns = [
            'temp', 'temp_min', 'temp_max', 'pressure', 'humidity',
            'wind_speed', 'wind_deg', 'rain_1h', 'rain_3h', 'snow_3h',
            'clouds_all', 'weather_main', 'weather_description'
        ]
        categorical_cols = ['weather_main', 'weather_description']

        locations = Location.objects.filter(active=True)
        self.stdout.write(f"Rozpoczynam ETL dla {locations.count()} lokalizacji...")

        for loc in locations:
            self.stdout.write(f"Pobieranie dla: {loc.city_name}...")

            # --- EXTRACT & TRANSFORM (Dane pogodowe) ---
            weather_data = fetch_and_map_weather(loc.latitude, loc.longitude)

            if weather_data:
                # --- TRANSFORM: klucze i wartości tekstowe na lowercase ---
                normalized = {}
                for k, v in weather_data.items():
                    k_lower = str(k).lower()
                    if isinstance(v, str):
                        normalized[k_lower] = v.lower()
                    else:
                        normalized[k_lower] = v
                weather_data = normalized

                # --- LOAD (Zapis pogody) ---
                try:
                    weather_log_instance = WeatherLog.objects.create(
                        location=loc,
                        **weather_data
                    )
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"Błąd zapisu WeatherLog dla {loc.city_name}: {e}"))
                    # nie przerywamy dalszego procesu, ale pomijamy predykcję jeśli brak weather_log_instance
                    weather_log_instance = None

                # --- PREDICTION (ML) ---
                try:
                    # 1. Przygotowanie danych pod model (tylko potrzebne kolumny)
                    input_data = {k: weather_data.get(k) for k in feature_columns}

                    # 2. Konwersja do DataFrame
                    df_features = pd.DataFrame([input_data])

                    # Uzupełnianie braków (prosty fallback; dopasuj do tego co robiłeś przy treningu)
                    df_features = df_features.fillna(0)

                    # 3. Kodowanie kolumn kategorycznych
                    # Jeśli mamy "cat_encoder" (np. ColumnTransformer / OneHotEncoder) — spróbujemy go użyć.
                    if cat_encoder is not None:
                        try:
                            # Jeżeli cat_encoder jest ColumnTransformer, trzeba go zastosować w taki sposób,
                            # by otrzymać jednakową reprezentację, jak podczas treningu.
                            # Zakładamy, że cat_encoder.transform akceptuje cały DataFrame.
                            transformed = cat_encoder.transform(df_features)
                            # Jeśli transform zwraca macierz (np. numpy), model prawdopodobnie oczekuje tej samej formy.
                            # W takim wypadku po prostu używamy transformed bez przeindeksowania kolumn.
                            # Więc przekazujemy do modelu jako DataFrame/ndarray.
                            df_for_model = transformed
                        except Exception as e:
                            self.stdout.write(self.style.WARNING(
                                f"Błąd przy użyciu cat_encoder: {e}. Spróbuję użyć label_encoders."
                            ))
                            cat_encoder = None  # wymusimy fallback
                            df_for_model = None
                    else:
                        df_for_model = None

                    # Fallback: użycie zapisanych label_encoders (pojedyncze enkodery na kolumnę)
                    if df_for_model is None:
                        for col in categorical_cols:
                            if col in df_features.columns:
                                if col in label_encoders and label_encoders[col] is not None:
                                    le = label_encoders[col]
                                    # Obsługa dwóch formatów: sklearn LabelEncoder lub dict mapping
                                    try:
                                        # sklearn LabelEncoder
                                        df_features[col] = le.transform(df_features[col].astype(str))
                                    except Exception:
                                        # mapping dict
                                        if isinstance(le, dict):
                                            df_features[col] = df_features[col].astype(str).map(le).fillna(0).astype(int)
                                        else:
                                            # nieznany format -> zamiana na indeksy i zapis mapy
                                            vals = df_features[col].astype(str).unique().tolist()
                                            mapping = {v: i for i, v in enumerate(vals)}
                                            df_features[col] = df_features[col].astype(str).map(mapping)
                                            label_encoders[col] = mapping
                                            joblib.dump(label_encoders, "label_encoders.pkl")
                                            self.stdout.write(self.style.WARNING(
                                                f"Utworzono nowy mapping dla kolumny {col} i zapisano label_encoders.pkl."
                                            ))
                                else:
                                    # brak encodera dla danej kolumny -> stwórz prosty mapping i zapisz go (UWAGA)
                                    vals = df_features[col].astype(str).unique().tolist()
                                    mapping = {v: i for i, v in enumerate(vals)}
                                    df_features[col] = df_features[col].astype(str).map(mapping)
                                    label_encoders[col] = mapping
                                    joblib.dump(label_encoders, "label_encoders.pkl")
                                    self.stdout.write(self.style.WARNING(
                                        f"Utworzono lokalny mapping dla {col} i zapisano label_encoders.pkl "
                                        "(może niezgodne z mapowaniem z treningu)."
                                    ))

                        # Teraz df_features jest gotowy jako DataFrame w kolejności feature_columns
                        # upewniamy się, że kolumny są w odpowiedniej kolejności
                        df_features = df_features[feature_columns]
                        df_for_model = df_features.values  # modele sklearn zwykle akceptują numpy array

                    # 4. Wykonanie predykcji
                    prediction_value = model_rf.predict(df_for_model)[0]

                    # 5. Zapis predykcji do bazy
                    if weather_log_instance:
                        Prediction.objects.create(
                            weather_log=weather_log_instance,
                            prediction=float(prediction_value)
                        )

                    self.stdout.write(self.style.SUCCESS(
                        f"Zapisano log i predykcję ({prediction_value:.2f}) dla {loc.city_name}"
                    ))

                except Exception as e:
                    self.stdout.write(self.style.WARNING(
                        f"Zapisano pogodę, ale błąd predykcji dla {loc.city_name}: {e}"
                    ))

            else:
                self.stdout.write(self.style.ERROR(f"Nie udało się pobrać danych dla {loc.city_name}"))

            # Rate limiting
            time.sleep(1)

        self.stdout.write(self.style.SUCCESS("Proces ETL zakończony."))
