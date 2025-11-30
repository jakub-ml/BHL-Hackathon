# weather_app/views.py
from django.shortcuts import render
from .services import get_open_meteo_data  # Zmieniona nazwa funkcji
from django.template import loader
from django.http import HttpResponse, JsonResponse
from .models import Prediction, Location
from .agents.askAgents import askAgents
import json

def weather_dashboard(request):
    context = {}

    city_input = request.POST.get('city')
    weather_data = get_open_meteo_data(city_input)

    # Pobieramy predykcje (wyszukane/posortowane)
    if city_input:
        prediction_result = Prediction.objects.select_related('weather_log__location') \
            .filter(weather_log__location__city_name__icontains=city_input) \
            .order_by('prediction')
    else:
        prediction_result = Prediction.objects.select_related('weather_log__location') \
            .all().order_by('prediction')

    # Pobieramy wszystkie aktywne lokalizacje (możesz zamiast .filter(active=True) użyć .all())
    locations_qs = Location.objects.filter(active=True).values('city_name', 'latitude', 'longitude')
    locations_list = list(locations_qs)  # konwertujemy QuerySet na listę dictów

    # Przygotowujemy listę predykcji do JS (można mieć wiele predykcji dla miasta)
    predictions_list = []
    for p in prediction_result:
        loc_name = p.weather_log.location.city_name
        predictions_list.append({
            'city': loc_name,
            'prediction': float(p.prediction)
        })

    # Serializujemy do JSON z ensure_ascii=False żeby zachować polskie znaki
    context.update({
        'weather_data': weather_data,
        'prediction': prediction_result,
        'city': weather_data.get('city_name', city_input) if weather_data else city_input,
        'locations_json': json.dumps(locations_list, ensure_ascii=False),
        'predictions_json': json.dumps(predictions_list, ensure_ascii=False),
    })

    if not weather_data:
        context['error'] = "Nie znaleziono miasta lub błąd API Open-Meteo."

    return render(request, 'dashboard.html', context)

def weather_dashboard_old(request):
    city_input = request.POST.get('city')
    weather_data = get_open_meteo_data(city_input)  # twoja funkcja, może zwracać None

    # Pobieramy predykcje (posortowane rosnąco)
    if city_input:
        prediction_qs = Prediction.objects.select_related('weather_log__location') \
            .filter(weather_log__location__city_name__icontains=city_input) \
            .order_by('prediction')
    else:
        prediction_qs = Prediction.objects.select_related('weather_log__location').all().order_by('prediction')

    # Lokacje — zwróć id, city_name, latitude, longitude (filter active jeśli chcesz)
    locations_qs = Location.objects.filter(active=True).values('id', 'city_name', 'latitude', 'longitude')
    locations_list = list(locations_qs)

    # Predykcje do JS – powiązane przez location_id
    predictions_list = []
    for p in prediction_qs:
        predictions_list.append({
            'location_id': p.weather_log.location_id,
            'prediction': float(p.prediction)
        })

    # Jeśli chcesz testować lokalnie bez danych DB — odkomentuj poniżej przykładowe dane
    # if not locations_list:
    #     locations_list = [{'id': 1, 'city_name': 'Warszawa', 'latitude': 52.2297, 'longitude': 21.0122}]
    # if not predictions_list:
    #     predictions_list = [{'location_id': 1, 'prediction': 10.0}]

    context = {
        'weather_data': weather_data,
        'prediction': prediction_qs,
        'city': (weather_data.get('city_name') if weather_data else city_input),
        'locations_json': json.dumps(locations_list, ensure_ascii=False),
        'predictions_json': json.dumps(predictions_list, ensure_ascii=False),
    }


    return render(request, 'dashboard_old.html', context)


def weather_dashboard_new(request):
    return render(request, "weather/dashboard_new.html")

def run_ai_analysis(request):
    if request.method == "POST":
        text = request.body.decode("utf-8")

        # 👉 tutaj wołasz dowolną funkcję Python!
        result = askAgents(text)
        print(result)

        return JsonResponse({"result": result})

    return JsonResponse({"error": "Only POST allowed"}, status=405)