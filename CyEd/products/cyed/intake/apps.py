from django.apps import AppConfig


class IntakeConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "products.cyed.intake"
    label = "cyed_intake"
    verbose_name = "CyEd — Document Intake (OCR)"
