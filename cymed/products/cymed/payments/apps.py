from django.apps import AppConfig


class PaymentsConfig(AppConfig):
    name = "products.cymed.payments"
    label = "cymed_payments"
    verbose_name = "CyMed Payments"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):
        from . import signals  # noqa: F401
