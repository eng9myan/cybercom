"""
CyMed Pharmacy Edition — Django App Configuration
"""
from django.apps import AppConfig


class PharmacyConfig(AppConfig):
    name = "products.cymed.pharmacy"
    label = "cymed_pharmacy"
    verbose_name = "CyMed Pharmacy Edition"

    def ready(self):
        # Register signal handlers
        import products.cymed.pharmacy.signals  # noqa: F401
