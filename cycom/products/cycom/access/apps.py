from django.apps import AppConfig


class AccessConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "products.cycom.access"
    label = "cycom_access"
    verbose_name = "Cycom — Access Control"
