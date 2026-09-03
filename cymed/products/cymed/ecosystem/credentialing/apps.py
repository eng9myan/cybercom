"""AppConfig for CyMed Ecosystem provider credentialing sub-app."""
from django.apps import AppConfig


class CredentialingConfig(AppConfig):
    name = "products.cymed.ecosystem.credentialing"
    label = "cymed_eco_credentialing"
    verbose_name = "CyMed Ecosystem — Provider Credentialing"
