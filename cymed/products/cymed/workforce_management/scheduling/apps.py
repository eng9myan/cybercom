from django.apps import AppConfig


class SchedulingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "products.cymed.workforce_management.scheduling"
    label = "cymed_hwm_scheduling"
    verbose_name = "CyMed Workforce Management — Scheduling"
