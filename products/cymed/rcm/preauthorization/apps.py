from django.apps import AppConfig


class PreauthorizationConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "backend.products.cymed.rcm.preauthorization"
    label = "cymed_rcm_preauthorization"
    verbose_name = "CyMed RCM - Preauthorization"
