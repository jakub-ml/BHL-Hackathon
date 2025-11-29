# weather_app/services.py
import requests
import datetime
import pytz


def get_wmo_description(code):
    """
    Mapuje kody WMO (Open-Meteo) na format OpenWeather (main, description, icon).
    """
    # Proste mapowanie dla przykładu.
    # Kodowanie WMO: https://open-meteo.com/en/docs
    mapping = {
        0: ('Clear', 'clear sky', '01d'),
        1: ('Clouds', 'mainly clear', '02d'),
        2: ('Clouds', 'partly cloudy', '03d'),
        3: ('Clouds', 'overcast', '04d'),
        45: ('Fog', 'fog', '50d'),
        48: ('Fog', 'depositing rime fog', '50d'),
        51: ('Drizzle', 'light drizzle', '09d'),
        53: ('Drizzle', 'moderate drizzle', '09d'),
        55: ('Drizzle', 'dense drizzle', '09d'),
        61: ('Rain', 'slight rain', '10d'),
        63: ('Rain', 'moderate rain', '10d'),
        65: ('Rain', 'heavy intensity rain', '10d'),
        71: ('Snow', 'slight snow', '13d'),
        73: ('Snow', 'moderate snow', '13d'),
        75: ('Snow', 'heavy snow', '13d'),
        80: ('Rain', 'light rain showers', '09d'),
        81: ('Rain', 'moderate rain showers', '09d'),
        82: ('Rain', 'violent rain showers', '09d'),
        95: ('Thunderstorm', 'thunderstorm', '11d'),
    }
    return mapping.get(code, ('Unknown', 'unknown', '50d'))


def get_coordinates(city_name):
    """Pobiera lat/lon dla miasta z Open-Meteo Geocoding API."""
    url = f"https://geocoding-api.open-meteo.com/v1/search?name={city_name}&count=1&language=pl&format=json"
    try:
        response = requests.get(url).json()
        if 'results' in response:
            data = response['results'][0]
            return data['latitude'], data['longitude'], data['name'], data['timezone']
    except Exception:
        pass
    return None, None, None, None


def get_open_meteo_data(city_input):
    # 1. Geocoding
    lat, lon, city_name, timezone_str = get_coordinates(city_input)
    if not lat:
        return None

    # 2. Pobranie danych pogodowych
    # Potrzebujemy:
    # - current: temp, pressure, wind, humidity, weather_code
    # - hourly: rain, snowfall (żeby policzyć sumy 3h)
    # - daily: temp_min, temp_max (bo 'current' tego nie ma)
    weather_url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,relative_humidity_2m,surface_pressure,wind_speed_10m,wind_direction_10m,rain,snowfall,cloud_cover,weather_code",
        "hourly": "rain,snowfall",
        "daily": "temperature_2m_max,temperature_2m_min",
        "timezone": timezone_str,
        "forecast_days": 1
    }

    resp = requests.get(weather_url, params=params)
    if resp.status_code != 200:
        return None

    data = resp.json()
    curr = data['current']
    daily = data['daily']
    hourly = data['hourly']

    # 3. Formatowanie Daty (dt_iso)
    # Open-Meteo zwraca czas w formacie ISO (np. 2023-10-25T14:00), ale bez offsetu w stringu,
    # mimo że poprosiliśmy o strefę czasową. Musimy to skleić.

    local_tz = pytz.timezone(timezone_str)
    # Parsujemy czas dostarczony przez API (który jest czasem lokalnym)
    dt_obj = datetime.datetime.fromisoformat(curr['time'])
    # Nadajemy mu strefę czasową (localize)
    dt_aware = local_tz.localize(dt_obj)

    # Format: 2015-01-01 00:00:00+01:00
    dt_iso_str = dt_aware.strftime('%Y-%m-%d %H:%M:%S%z')
    # Fix na dwukropek w strefie czasowej (+0100 -> +01:00)
    if dt_iso_str[-3] != ':':
        dt_iso_str = dt_iso_str[:-2] + ':' + dt_iso_str[-2:]

    # 4. Obliczenia Rain/Snow 3h
    # Znajdujemy indeks aktualnej godziny w tablicy hourly
    try:
        current_hour_idx = hourly['time'].index(curr['time'])
        # Pobieramy sumę z 3 ostatnich godzin (bieżąca + 2 wstecz)
        # Zabezpieczamy index żeby nie wyszedł poza zakres < 0
        start_idx = max(0, current_hour_idx - 2)

        # Slicing w pythonie [start:stop] (stop jest exclusive, więc +1)
        rain_3h = sum(hourly['rain'][start_idx: current_hour_idx + 1])
        snow_3h = sum(hourly['snowfall'][start_idx: current_hour_idx + 1])
    except ValueError:
        rain_3h = 0.0
        snow_3h = 0.0

    # 5. Mapowanie WMO do formatu OpenWeather
    wmo_code = curr['weather_code']
    w_main, w_desc, w_icon = get_wmo_description(wmo_code)

    # 6. Finalna struktura (squerowanie danych)
    mapped_data = {
        'dt_iso': dt_iso_str,
        'city_name': city_name,
        'temp': curr['temperature_2m'],
        'temp_min': daily['temperature_2m_min'][0],  # Z tablicy daily
        'temp_max': daily['temperature_2m_max'][0],  # Z tablicy daily
        'pressure': curr['surface_pressure'],
        'humidity': curr['relative_humidity_2m'],
        'wind_speed': curr['wind_speed_10m'],
        # m/s lub km/h zależnie od ustawień (domyślnie km/h w OpenMeteo, warto sprawdzić jednostki modelu!)
        'wind_deg': curr['wind_direction_10m'],
        'rain_1h': curr['rain'],  # OpenMeteo podaje rain w mm z ostatniej godziny w current
        'rain_3h': round(rain_3h, 2),
        'snow_3h': round(snow_3h, 2),
        'clouds_all': curr['cloud_cover'],
        'weather_id': wmo_code,  # Tutaj zostawiamy kod WMO jako ID, bo to numeryczny identyfikator
        'weather_main': w_main,
        'weather_description': w_desc,
        'weather_icon': w_icon
    }

    return mapped_data


def fetch_and_map_weather(lat, lon, timezone_str="Europe/Warsaw"):
    """
    Pobiera dane dla konkretnych współrzędnych i mapuje do schematu.
    Zwraca słownik gotowy do zapisu w modelu WeatherLog.
    """
    # URL Forecast (zawiera current, hourly i daily)
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,relative_humidity_2m,surface_pressure,wind_speed_10m,wind_direction_10m,rain,snowfall,cloud_cover,weather_code",
        "hourly": "rain,snowfall",
        "daily": "temperature_2m_max,temperature_2m_min",
        "timezone": timezone_str,
        "forecast_days": 1
    }

    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"Błąd API dla {lat}, {lon}: {e}")
        return None

    curr = data['current']
    daily = data['daily']
    hourly = data['hourly']

    # Logika daty
    local_tz = pytz.timezone(timezone_str)
    dt_obj = datetime.datetime.fromisoformat(curr['time'])
    dt_aware = local_tz.localize(dt_obj)
    dt_iso_str = dt_aware.strftime('%Y-%m-%d %H:%M:%S%z')
    if dt_iso_str[-3] != ':':
        dt_iso_str = dt_iso_str[:-2] + ':' + dt_iso_str[-2:]

    # Logika sumy opadów 3h
    try:
        current_hour_idx = hourly['time'].index(curr['time'])
        start_idx = max(0, current_hour_idx - 2)
        rain_3h = sum(hourly['rain'][start_idx : current_hour_idx + 1])
        snow_3h = sum(hourly['snowfall'][start_idx : current_hour_idx + 1])
    except ValueError:
        rain_3h = 0.0
        snow_3h = 0.0

    wmo_code = curr['weather_code']
    w_main, w_desc, w_icon = get_wmo_description(wmo_code)

    return {
        'dt_iso': dt_iso_str,
        'temp': curr['temperature_2m'],
        'temp_min': daily['temperature_2m_min'][0],
        'temp_max': daily['temperature_2m_max'][0],
        'pressure': curr['surface_pressure'],
        'humidity': curr['relative_humidity_2m'],
        'wind_speed': curr['wind_speed_10m'],
        'wind_deg': curr['wind_direction_10m'],
        'rain_1h': curr['rain'],
        'rain_3h': round(rain_3h, 2),
        'snow_3h': round(snow_3h, 2),
        'clouds_all': curr['cloud_cover'],
        'weather_id': wmo_code,
        'weather_main': w_main,
        'weather_description': w_desc,
        'weather_icon': w_icon
    }