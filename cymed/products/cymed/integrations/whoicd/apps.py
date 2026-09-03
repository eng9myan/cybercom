from django.apps import AppConfig


class WHOICDConfig(AppConfig):
    name = "products.cymed.integrations.whoicd"
    label = "cymed_int_whoicd"
    verbose_name = "CyMed WHO ICD-11 Bridge"
    default_auto_field = "django.db.models.BigAutoField"
