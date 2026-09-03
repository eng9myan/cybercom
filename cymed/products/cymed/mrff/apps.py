"""Parent app config for products.cymed.mrff — no models of its own."""
from django.apps import AppConfig


class MrffConfig(AppConfig):
    name = "products.cymed.mrff"
    label = "cymed_mrff"
    verbose_name = "CyMed MRFF Program"
