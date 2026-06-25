from django.apps import AppConfig


class ForecastingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "products.cymed.workforce_management.forecasting"
    label = "cymed_hwm_forecasting"
    verbose_name = "CyMed Workforce Management — Predictive Staffing Forecasting"
