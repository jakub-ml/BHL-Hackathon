from django.urls import path
from .views import weather_dashboard, run_ai_analysis

urlpatterns = [
    path('weather/', weather_dashboard, name='weather_dashboard'),
    path('run-ai/', run_ai_analysis, name='run_ai'),
]
