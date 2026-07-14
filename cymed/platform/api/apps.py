from django.apps import AppConfig


class ApiConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "platform.api"
    label = "platform_api"
    verbose_name = "Platform API"
