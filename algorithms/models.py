from django.db import models


class Location(models.Model):
    city_name = models.CharField(max_length=100)
    latitude = models.FloatField()
    longitude = models.FloatField()
    active = models.BooleanField(default=True)  # Flaga, czy pobierać dane dla tego miejsca

    def __str__(self):
        return self.city_name


class WeatherLog(models.Model):
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='weather_logs')
    created_at = models.DateTimeField(auto_now_add=True)  # Kiedy pobrano dane

    # Pola z Twojej specyfikacji
    dt_iso = models.CharField(max_length=50)  # Przechowujemy jako string z offsetem
    temp = models.FloatField()
    temp_min = models.FloatField()
    temp_max = models.FloatField()
    pressure = models.FloatField()
    humidity = models.IntegerField()
    wind_speed = models.FloatField()
    wind_deg = models.IntegerField()
    rain_1h = models.FloatField(default=0.0)
    rain_3h = models.FloatField(default=0.0)
    snow_3h = models.FloatField(default=0.0)
    clouds_all = models.IntegerField()
    weather_id = models.IntegerField()
    weather_main = models.CharField(max_length=50)
    weather_description = models.CharField(max_length=100)
    weather_icon = models.CharField(max_length=10)

    def __str__(self):
        return f"{self.location.city_name} - {self.dt_iso}"