"""NPHIES interaction audit trail."""
from django.db import models

from platform.common.models import BaseModel


class NphiesInteraction(BaseModel):
    KIND_CHOICES = [
        ("eligibility", "Coverage Eligibility Request"),
        ("preauth_submit", "Pre-Auth Submit"),
        ("preauth_status", "Pre-Auth Status"),
        ("claim_submit", "Claim Submit"),
        ("remittance", "Remittance Advice"),
    ]
    STATUS_CHOICES = [
        ("sent", "Sent"),
        ("succeeded", "Succeeded"),
        ("failed", "Failed"),
    ]

    kind = models.CharField(max_length=30, choices=KIND_CHOICES, db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, db_index=True)
    licensee_id = models.CharField(max_length=100, blank=True)
    correlation_id = models.CharField(max_length=100, db_index=True, blank=True)
    request_bundle = models.JSONField(default=dict)
    response_bundle = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)
    duration_ms = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = "cymed_nphies_interactions"
        ordering = ["-created_at"]
