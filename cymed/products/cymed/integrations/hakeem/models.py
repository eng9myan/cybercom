"""Hakeem message audit."""
from django.db import models

from platform.common.models import BaseModel


class HakeemMessage(BaseModel):
    DIRECTIONS = [("pull", "Pull from Hakeem"), ("push", "Push to Hakeem")]
    TRANSPORTS = [("rpc", "VistaRPC"), ("sftp_hl7", "SFTP HL7 v2"), ("fhir", "FHIR (2026)")]
    STATUSES = [("pending", "Pending"), ("succeeded", "Succeeded"), ("failed", "Failed")]

    direction = models.CharField(max_length=10, choices=DIRECTIONS)
    transport = models.CharField(max_length=20, choices=TRANSPORTS)
    op = models.CharField(max_length=100, db_index=True)
    subject_national_id = models.CharField(max_length=30, blank=True, db_index=True)
    request_payload = models.TextField(blank=True)
    response_payload = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUSES, default="pending")
    error_message = models.TextField(blank=True)
    duration_ms = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = "cymed_hakeem_messages"
        ordering = ["-created_at"]
