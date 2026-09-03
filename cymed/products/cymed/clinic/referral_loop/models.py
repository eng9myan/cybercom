"""Closed-loop referral tracking across ecosystem providers."""
from django.db import models

from platform.common.models import BaseModel, SoftDeleteMixin


class Referral(BaseModel, SoftDeleteMixin):
    STATUS = [
        ("draft", "Draft"),
        ("sent", "Sent"),
        ("acknowledged", "Acknowledged"),
        ("scheduled", "Appointment scheduled"),
        ("completed", "Care completed"),
        ("result_shared", "Result shared back"),
        ("declined", "Declined"),
        ("expired", "Expired"),
    ]
    SPECIALTY_KIND = [
        ("hospital", "Hospital"), ("clinic", "Clinic"),
        ("lab", "Lab"), ("imaging", "Imaging"),
        ("pharmacy", "Pharmacy"),
    ]

    from_tenant_id = models.UUIDField(db_index=True)
    from_practitioner_id = models.UUIDField(null=True, blank=True)
    to_tenant_id = models.UUIDField(db_index=True)
    to_practitioner_id = models.UUIDField(null=True, blank=True)
    target_kind = models.CharField(max_length=20, choices=SPECIALTY_KIND)

    patient_profile_id = models.UUIDField(db_index=True)
    encounter_id = models.UUIDField(null=True, blank=True)
    reason = models.CharField(max_length=400)
    clinical_summary = models.TextField(blank=True)
    urgency = models.CharField(max_length=20,
                                choices=[("routine", "Routine"),
                                         ("urgent", "Urgent"),
                                         ("stat", "STAT")],
                                default="routine")
    status = models.CharField(max_length=20, choices=STATUS, default="draft", db_index=True)

    sent_at = models.DateTimeField(null=True, blank=True)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    scheduled_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    result_shared_at = models.DateTimeField(null=True, blank=True)

    result_documents = models.JSONField(default=list, blank=True)   # [{name, url}]
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "cymed_clinic_referral_loop_referrals"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["patient_profile_id", "status"]),
            models.Index(fields=["from_tenant_id", "status"]),
            models.Index(fields=["to_tenant_id", "status"]),
        ]
