from django.apps import AppConfig


class ReportingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "products.cymed.population_health.reporting"
    label = "cymed_ph_reporting"
    verbose_name = "CyMed Population Health — Reporting"
