"""App config for CyMed Imaging patient booking sub-app."""

from django.apps import AppConfig


class PatientBookingConfig(AppConfig):
    name = "products.cymed.imaging.patient_booking"
    label = "cymed_img_patient_booking"
    verbose_name = "CyMed Imaging — Patient Imaging Booking"
