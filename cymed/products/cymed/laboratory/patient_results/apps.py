"""Django app config for CyMed Laboratory patient results portal."""
from django.apps import AppConfig


class PatientResultsConfig(AppConfig):
    name = "products.cymed.laboratory.patient_results"
    label = "cymed_lab_patient_results"
    verbose_name = "CyMed Laboratory — Patient Results Portal"
