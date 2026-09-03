"""Kiosk-based patient self check-in."""
from django.db import models

from platform.common.models import BaseModel


class KioskSession(BaseModel):
    STAGES = [
        ("started", "Started"),
        ("identified", "Patient identified"),
        ("insurance_verified", "Insurance verified"),
        ("consent_signed", "Consent signed"),
        ("completed", "Completed"),
        ("abandoned", "Abandoned"),
        ("failed_verify", "Insurance failed — see staff"),
    ]

    kiosk_id = models.CharField(max_length=100, db_index=True)
    appointment_id = models.UUIDField(db_index=True, null=True, blank=True)
    patient_profile_id = models.UUIDField(db_index=True, null=True, blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    stage = models.CharField(max_length=30, choices=STAGES, default="started")
    identity_method = models.CharField(max_length=30, blank=True,
                                        help_text="nfc | qr | national_id | phone_otp")
    duration_seconds = models.IntegerField(null=True, blank=True)
    error_note = models.CharField(max_length=400, blank=True)

    class Meta:
        db_table = "cymed_clinic_kiosk_sessions"
        ordering = ["-started_at"]
