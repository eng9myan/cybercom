from django.apps import AppConfig


class CohortsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "products.cymed.population_health.cohorts"
    label = "cymed_ph_cohorts"
    verbose_name = "CyMed Population Health — Cohorts"
