from django.apps import AppConfig


class SelfCheckinConfig(AppConfig):
    name = "products.cymed.clinic.self_checkin"
    label = "cymed_clinic_self_checkin"
    verbose_name = "CyMed Clinic Self-Check-in Kiosk"
    default_auto_field = "django.db.models.BigAutoField"
