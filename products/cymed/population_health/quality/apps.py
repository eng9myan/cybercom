from django.apps import AppConfig


class QualityConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "products.cymed.population_health.quality"
    label = "cymed_ph_quality"
    verbose_name = "CyMed Population Health — Quality"
