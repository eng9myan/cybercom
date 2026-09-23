from django.apps import AppConfig


class ReportingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "products.cycom.reporting"
    label = "cycom_reporting"
    verbose_name = "Cycom — Custom Reports (BI)"
