"""App config for CyMed Imaging AI triage and model registry."""

from django.apps import AppConfig


class AiTriageConfig(AppConfig):
    name = "products.cymed.imaging.ai_triage"
    label = "cymed_img_ai_triage"
    verbose_name = "CyMed Imaging — AI Triage & Model Registry"
