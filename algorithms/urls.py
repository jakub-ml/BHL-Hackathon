from django.urls import path
from .views import weather_dashboard, run_ai_analysis, calc_api

urlpatterns = [
    path('weather/', weather_dashboard, name='weather_dashboard'),
    path('run-ai/', run_ai_analysis, name='run_ai'),
    path("api/", calc_api, name="calc_api")

]
