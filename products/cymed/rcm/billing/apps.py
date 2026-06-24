from django.apps import AppConfig


class BillingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "backend.products.cymed.rcm.billing"
    label = "cymed_rcm_billing"
    verbose_name = "CyMed RCM - Billing"
