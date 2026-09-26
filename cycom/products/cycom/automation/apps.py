from django.apps import AppConfig


class AutomationConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "products.cycom.automation"
    label = "cycom_automation"
    verbose_name = "Cycom — Automation"

    def ready(self):
        from products.cycom.automation import signals

        signals.connect()
