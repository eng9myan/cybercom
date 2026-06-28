from django.apps import AppConfig


class PricingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "products.cymed.rcm.pricing"
    label = "cymed_rcm_pricing"
    verbose_name = "CyMed RCM - Pricing"
