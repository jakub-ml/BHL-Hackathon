# weather_app/views.py
from django.shortcuts import render
from .services import get_open_meteo_data  # Zmieniona nazwa funkcji
from .ml_model import WeatherPredictor
from django.template import loader
from django.http import HttpResponse


def weather_dashboard(request):
    context = {}
    if request.method == 'POST':
        city_input = request.POST.get('city')

        # Pobieranie danych pogodowych
        weather_data = get_open_meteo_data(city_input)

        if weather_data:
            prediction_result = WeatherPredictor.predict(weather_data)

            context = {
                'weather_data': weather_data,
                'prediction': prediction_result,
                'city': weather_data.get('city_name', city_input)
            }
        else:
            context['error'] = "Nie znaleziono miasta lub błąd API Open-Meteo."

    return render(request, 'dashboard.html', context)