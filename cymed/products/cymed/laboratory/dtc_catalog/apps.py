"""App config for CyMed Laboratory DTC Test Catalog sub-app."""
from django.apps import AppConfig


class DtcCatalogConfig(AppConfig):
    name = "products.cymed.laboratory.dtc_catalog"
    label = "cymed_lab_dtc_catalog"
    verbose_name = "CyMed Laboratory — DTC Test Catalog"
