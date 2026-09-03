"""Django app config for CyMed MRFF diagnostic and imaging AI sub-app."""
from django.apps import AppConfig


class AiDiagnosticsConfig(AppConfig):
    name = "products.cymed.mrff.ai_diagnostics"
    label = "cymed_mrff_ai_diagnostics"
    verbose_name = "CyMed MRFF — Diagnostic & Imaging AI"
