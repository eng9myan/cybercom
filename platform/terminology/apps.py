from django.apps import AppConfig


class TerminologyConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "platform.terminology"
    label = "platform_terminology"

    def ready(self):
        # Import providers module to trigger registration of default providers in registry
        pass
