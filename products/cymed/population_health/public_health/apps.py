from django.apps import AppConfig


class PublicHealthConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "products.cymed.population_health.public_health"
    label = "cymed_ph_public_health"
    verbose_name = "CyMed Population Health — Public Health"