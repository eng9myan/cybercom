from django.apps import AppConfig


class MaintenanceConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "products.cycom.maintenance"
    label = "cycom_maintenance"
    verbose_name = "Cycom — Maintenance"
