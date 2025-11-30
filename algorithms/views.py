# weather_app/views.py
from django.shortcuts import render
from .services import get_open_meteo_data  # Zmieniona nazwa funkcji
from django.template import loader
from django.http import HttpResponse, JsonResponse
from .models import Prediction
from .agents.askAgents import askAgents
def weather_dashboard(request):
    context = {}

    city_input = request.POST.get('city')

    # Pobieranie danych pogodowych
    weather_data = get_open_meteo_data(city_input)

    if weather_data:
        # Pobieramy predykcje posortowane rosnąco po wartości prediction (najmniejsza emisja / koszt najpierw)
        # Używamy select_related żeby załadować weather_log i location jednym zapytaniem
        if city_input:
            # opcjonalnie: jeśli podano miasto, filtrujemy po nazwie lokalizacji (case-insensitive, partial match)
            prediction_result = Prediction.objects.select_related('weather_log__location') \
                .filter(weather_log__location__city_name__icontains=city_input) \
                .order_by('prediction')
        else:
            prediction_result = Prediction.objects.select_related('weather_log__location') \
                .all().order_by('prediction')

        context = {
            'weather_data': weather_data,
            'prediction': prediction_result,
            'city': weather_data.get('city_name', city_input)
        }
    else:
        context['error'] = "Nie znaleziono miasta lub błąd API Open-Meteo."

    return render(request, 'dashboard.html', context)


def run_ai_analysis(request):
    if request.method == "POST":
        text = request.body.decode("utf-8")

        # 👉 tutaj wołasz dowolną funkcję Python!
        result = askAgents(text)
        print(result)

        return JsonResponse({"result": result})

    return JsonResponse({"error": "Only POST allowed"}, status=405)