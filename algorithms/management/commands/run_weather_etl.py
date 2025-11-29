from django.core.management.base import BaseCommand
from algorithms.models import Location, WeatherLog
from algorithms.services import fetch_and_map_weather
import time


class Command(BaseCommand):
    help = 'Pobiera dane pogodowe dla wszystkich aktywnych lokalizacji'

    def handle(self, *args, **kwargs):
        locations = Location.objects.filter(active=True)
        self.stdout.write(f"Rozpoczynam ETL dla {locations.count()} lokalizacji...")

        for loc in locations:
            self.stdout.write(f"Pobieranie dla: {loc.city_name}...")

            # EXTRACT & TRANSFORM
            weather_data = fetch_and_map_weather(loc.latitude, loc.longitude)

            if weather_data:
                # LOAD
                WeatherLog.objects.create(
                    location=loc,
                    **weather_data
                )
                self.stdout.write(self.style.SUCCESS(f"Zapisano dane dla {loc.city_name}"))
            else:
                self.stdout.write(self.style.ERROR(f"Nie udało się pobrać danych dla {loc.city_name}"))

            # Dobra praktyka: opóźnienie, żeby nie zajechać API (rate limiting)
            time.sleep(1)

        self.stdout.write(self.style.SUCCESS("Proces ETL zakończony."))