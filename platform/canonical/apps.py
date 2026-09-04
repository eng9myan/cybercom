from django.apps import AppConfig


class CanonicalConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "platform.canonical"
    label = "platform_canonical"
    verbose_name = "Canonical Data Model (v1)"
