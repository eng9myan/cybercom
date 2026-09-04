from django.apps import AppConfig


class EInvoicingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "platform.einvoicing"
    label = "platform_einvoicing"
    verbose_name = "E-Invoicing Clearance Engine"
