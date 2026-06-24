rom django.apps import AppConfig


class SurveillanceConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "products.cymed.population_health.surveillance"
    label = "cymed_ph_surveillance"
    verbose_name = "CyMed Population Health — Surveillance"
