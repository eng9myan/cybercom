"""CyMed Pharmacy Compounding app config."""
from django.apps import AppConfig


class CompoundingConfig(AppConfig):
    name = "products.cymed.pharmacy.compounding"
    label = "cymed_pharmacy_compounding"
    verbose_name = "CyMed Pharmacy - Compounding Workflow"
