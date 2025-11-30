from django.urls import path
from .views import weather_dashboard, run_ai_analysis, weather_dashboard_old
from django.views.generic import TemplateView
urlpatterns = [
    path('weather/', weather_dashboard, name='weather_dashboard'),
    path('run-ai/', run_ai_analysis, name='run_ai'),
    path("weather/dashboard_old.html",
        weather_dashboard_old,
         name="weather_dashboard_old_html"),

    path("weather/dashboard_new.html",
             TemplateView.as_view(template_name="dashboard_new.html"),
             name="weather_dashboard_new_html"),
]
