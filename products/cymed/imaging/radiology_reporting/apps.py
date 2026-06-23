from django.apps import AppConfig


class RadiologyReportingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "products.cymed.imaging.radiology_reporting"
    label = "img_reporting"
    verbose_name = "CyMed Imaging — Radiology Reporting"
