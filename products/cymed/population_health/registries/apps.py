from django.apps import AppConfig


class RegistriesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "products.cymed.population_health.registries"
    label = "cymed_ph_registries"
    verbose_name = "CyMed Population Health — Registries"
