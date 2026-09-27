from django.apps import AppConfig


class CustomFieldsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "products.cycom.customfields"
    label = "cycom_customfields"
    verbose_name = "Cycom — Custom Fields"
