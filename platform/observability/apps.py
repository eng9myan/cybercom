from django.apps import AppConfig


class ObservabilityConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "platform.observability"
    label = "platform_observability"
    verbose_name = "Platform Observability"
