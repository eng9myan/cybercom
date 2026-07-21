from django.apps import AppConfig


class LocalizationConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "products.cycom.localization"
    label = "cycom_localization"
    verbose_name = "Cycom — Localization (multi-country billing)"
