from django.apps import AppConfig


class DigitalHealthConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "products.cymed.population_health.digital_health"
    label = "cymed_ph_digital_health"
    verbose_name = "CyMed Population Health — Digital Health"
