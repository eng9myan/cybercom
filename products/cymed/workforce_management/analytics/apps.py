from django.apps import AppConfig


class AnalyticsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "products.cymed.workforce_management.analytics"
    label = "cymed_hwm_analytics"
    verbose_name = "CyMed Workforce Management — Analytics"
