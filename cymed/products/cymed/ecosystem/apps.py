"""Parent app config for products.cymed.ecosystem — no models of its own."""
from django.apps import AppConfig

class EcosystemConfig(AppConfig):
    name = "products.cymed.ecosystem"
    label = "cymed_eco"
    verbose_name = "CyMed Ecosystem"
