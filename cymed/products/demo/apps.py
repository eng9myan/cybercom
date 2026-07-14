from django.apps import AppConfig


class DemoPlatformConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "products.demo"
    label = "cybercom_demo"
    verbose_name = "CyberCom Sales Demo Platform"
