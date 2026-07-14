from django.apps import AppConfig


class ImplementationConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "products.implementation"
    label = "cybercom_implementation"
    verbose_name = "CyberCom Implementation Methodology"
