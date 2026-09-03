"""AppConfig for the CyMed MRFF Ambient Scribe sub-app."""

from django.apps import AppConfig


class AmbientScribeConfig(AppConfig):
    name = "products.cymed.mrff.ambient_scribe"
    label = "cymed_mrff_ambient_scribe"
    verbose_name = "CyMed MRFF — Ambient Scribe & Auto-Summary"
