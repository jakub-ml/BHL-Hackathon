from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


class Location(models.Model):
    """
    Opcjonalny model lokalizacji/stacji pogodowej.
    Jeśli nie potrzebujesz lokalizacji, możesz go usunąć i ustawić location = None/omit.
    """
    name = models.CharField(max_length=200)
    latitude = models.DecimalField(max_digits=8, decimal_places=5, null=True, blank=True)
    longitude = models.DecimalField(max_digits=8, decimal_places=5, null=True, blank=True)

    def __str__(self):
        return self.name


class WeatherObservation(models.Model):
    # --- wyboru / enumy ---
    class Cloudiness(models.TextChoices):
        CLEAR = "CLR", "Bezchmurnie"
        FEW = "FEW", "Małe zachmurzenie"
        SCATTERED = "SCT", "Rozproszone"
        BROKEN = "BKN", "Duże zachmurzenie"
        OVERCAST = "OVC", "Całkowite zachmurzenie"
        FOG = "FG", "Mgła"

    class PrecipitationType(models.TextChoices):
        NONE = "NONE", "Brak"
        RAIN = "RAIN", "Deszcz"
        SNOW = "SNOW", "Śnieg"
        SLEET = "SLEET", "Marznący deszcz/deszcz ze śniegiem"
        HAIL = "HAIL", "Grad"
        DRIZZLE = "DRZ", "Mżawka"

    # --- pola podstawowe ---
    timestamp = models.DateTimeField(
        default=timezone.now,
        help_text="Data i czas obserwacji (UTC lub lokalny w zależności od ustawień)."
    )
    location = models.ForeignKey(
        Location, on_delete=models.CASCADE, null=True, blank=True,
        help_text="Opcjonalna lokalizacja/stacja."
    )

    temperature = models.DecimalField(
        max_digits=5, decimal_places=2,
        help_text="Temperatura w °C.",
        validators=[MinValueValidator(-100), MaxValueValidator(100)]
    )

    cloudiness = models.CharField(
        max_length=3,
        choices=Cloudiness.choices,
        default=Cloudiness.CLEAR,
        help_text="Typ/zachmurzenie (wybór)."
    )

    precipitation_type = models.CharField(
        max_length=5,
        choices=PrecipitationType.choices,
        default=PrecipitationType.NONE,
        help_text="Rodzaj opadów."
    )

    precipitation_amount = models.DecimalField(
        max_digits=6, decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0)],
        help_text="Ilość opadu w mm (np. suma opadu w okresie obserwacji)."
    )

    # wiatr
    wind_speed = models.DecimalField(
        max_digits=6, decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Prędkość wiatru w km/h."
    )

    wind_direction = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(359)],
        null=True, blank=True,
        help_text="Kierunek wiatru w stopniach (0 = północ, 90 = wschód, ...)."
    )

    # dodatkowe (opcjonalne)
    humidity = models.DecimalField(
        max_digits=5, decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        null=True, blank=True,
        help_text="Wilgotność względna w % (opcjonalne)."
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["timestamp"]),
            models.Index(fields=["location", "timestamp"]),
        ]
        # jeżeli chcesz zapewnić unikalność obserwacji per lokalizacja + timestamp:
        # unique_together = ("location", "timestamp")

    def __str__(self):
        loc = f" @ {self.location}" if self.location else ""
        return f"{self.timestamp.isoformat()} — {self.temperature}°C{loc}"

    # --- metody pomocnicze ---
    def wind_direction_compass(self) -> str:
        """Zwraca kierunek wiatru jako nazwę kompasa (N, NNE, NE, ...)."""
        if self.wind_direction is None:
            return "Brak danych"
        dirs = [
            "N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
            "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"
        ]
        idx = int((self.wind_direction + 11.25) / 22.5) % 16
        return dirs[idx]

    def is_precipitating(self) -> bool:
        """Czy występują opady (typ ≠ NONE lub ilość > 0)."""
        return (self.precipitation_type != self.PrecipitationType.NONE) or (self.precipitation_amount and float(self.precipitation_amount) > 0)

    def as_dict(self):
        """Szybki serializator do JSON-serializowalnej struktury (przydatne do API)."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "location": self.location.name if self.location else None,
            "temperature_c": float(self.temperature),
            "cloudiness": self.get_cloudiness_display(),
            "precipitation_type": self.get_precipitation_type_display(),
            "precipitation_amount_mm": float(self.precipitation_amount),
            "wind_speed_kmh": float(self.wind_speed),
            "wind_direction_deg": self.wind_direction,
            "wind_direction_compass": self.wind_direction_compass(),
            "humidity_percent": float(self.humidity) if self.humidity is not None else None,
        }