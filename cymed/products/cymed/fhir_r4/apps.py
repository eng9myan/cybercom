from django.apps import AppConfig


class FhirR4Config(AppConfig):
    name = "products.cymed.fhir_r4"
    label = "cymed_fhir_r4"
    verbose_name = "CyMed FHIR R4 Server"
    default_auto_field = "django.db.models.BigAutoField"
