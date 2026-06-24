from django.apps import AppConfig


class AnalyticsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "products.cymed.population_health.analytics"
    label = "cymed_ph_analytics"
    verbose_name = "CyMed Population Health — Analytics"
