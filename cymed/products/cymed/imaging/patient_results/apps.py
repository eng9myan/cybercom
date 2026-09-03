"""App config for CyMed Imaging patient results sub-app."""
from django.apps import AppConfig


class PatientResultsConfig(AppConfig):
    name = "products.cymed.imaging.patient_results"
    label = "cymed_img_patient_results"
    verbose_name = "CyMed Imaging - Patient Imaging Results"
