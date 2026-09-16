from django.db import models

from platform.common.models import BaseModel


class AuditEvent(BaseModel):
    """
    Immutable, append-only audit trail for CRUD on sensitive records (student
    PII, grades, wellbeing/health). Written by AuditedTenantViewSet; there is no
    API path to update or delete an AuditEvent (ST4S §6 — WORM-style logging).
    """

    ACTION_CHOICES = [
        ("create", "Create"),
        ("update", "Update"),
        ("delete", "Delete"),
        ("read_sensitive", "Sensitive Read"),
    ]

    actor = models.CharField(max_length=255, blank=True)  # authenticated user email/id
    actor_roles = models.CharField(max_length=255, blank=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    model_label = models.CharField(max_length=100)  # e.g. "cyed_sis.Student"
    object_id = models.CharField(max_length=64, blank=True)
    summary = models.CharField(max_length=500, blank=True)

    class Meta:
        db_table = "cyed_audit_events"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["tenant_id", "model_label"]),
            models.Index(fields=["tenant_id", "object_id"]),
        ]

    def __str__(self):
        return f"{self.action} {self.model_label}#{self.object_id} by {self.actor}"


class ConsentRecord(BaseModel):
    """
    Guardian/student consent for data collection and AI use (Australian Framework
    for Generative AI in Schools; APP 3/5). AI endpoints that operate on a named
    student require an active `ai_use` consent.
    """

    CONSENT_TYPES = [
        ("data_collection", "Data Collection"),
        ("ai_use", "Generative AI Use"),
        ("media", "Media / Photography"),
        ("excursion", "Excursion"),
    ]

    student = models.ForeignKey(
        "cyed_sis.Student", on_delete=models.CASCADE, related_name="consents"
    )
    consent_type = models.CharField(max_length=30, choices=CONSENT_TYPES)
    granted = models.BooleanField(default=False)
    granted_by = models.CharField(max_length=255, blank=True)  # guardian name/email
    method = models.CharField(max_length=100, blank=True)  # e.g. "portal", "signed form"
    note = models.TextField(blank=True)
    decided_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "cyed_consent_records"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant_id", "student", "consent_type"],
                name="uniq_consent_per_student_type",
            )
        ]

    def __str__(self):
        return f"{self.consent_type}={'granted' if self.granted else 'withheld'} ({self.student_id})"
