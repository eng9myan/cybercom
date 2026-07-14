from django.apps import AppConfig


class DICOMRegistryConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "products.cymed.imaging.dicom_registry"
    label = "img_dicom"
    verbose_name = "CyMed Imaging — DICOM Registry"
