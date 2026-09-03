"""Domain models for CyMed Imaging AI triage and model registry."""

from __future__ import annotations

import uuid
from decimal import Decimal

from django.db import models
from django.utils import timezone

from platform.common.models import BaseModel


class AiModel(BaseModel):
    class RegulatoryKind(models.TextChoices):
        FDA_CLEARED = "fda_cleared", "FDA Cleared"
        CE_MARKED = "ce_marked", "CE Marked"
        TGA_INCLUDED = "tga_included", "TGA Included"
        SFDA_CLEARED = "sfda_cleared", "SFDA Cleared"
        RESEARCH_ONLY = "research_only", "Research Only"
        UNKNOWN = "unknown", "Unknown"

    class AuthKind(models.TextChoices):
        NONE = "none", "None"
        BEARER = "bearer", "Bearer"
        MTLS = "mtls", "mTLS"
        API_KEY = "api_key", "API Key"

    tenant_id = models.UUIDField(null=True, blank=True, db_index=True)
    vendor = models.CharField(max_length=128)
    product_code = models.CharField(max_length=64)
    version = models.CharField(max_length=32)
    modality = models.CharField(max_length=32)
    body_part = models.CharField(max_length=64, blank=True)
    finding_kinds = models.JSONField(default=list, blank=True)
    regulatory_kind = models.CharField(
        max_length=32,
        choices=RegulatoryKind.choices,
        default=RegulatoryKind.UNKNOWN,
    )
    regulatory_reference = models.CharField(max_length=255, blank=True)
    endpoint_url = models.URLField(blank=True)
    auth_kind = models.CharField(
        max_length=32,
        choices=AuthKind.choices,
        default=AuthKind.NONE,
    )
    auth_secret_ref = models.CharField(max_length=128, blank=True)
    enabled = models.BooleanField(default=True)

    class Meta:
        db_table = "cymed_img_ai_triage_ai_model"
        unique_together = [("vendor", "product_code", "version")]

    def __str__(self) -> str:
        return f"{self.vendor}/{self.product_code}@{self.version}"


class TriageQueue(BaseModel):
    tenant_id = models.UUIDField(db_index=True)
    code = models.CharField(max_length=64)
    name = models.CharField(max_length=128)
    modality = models.CharField(max_length=32)
    priority_rules = models.JSONField(default=dict, blank=True)
    active = models.BooleanField(default=True)

    class Meta:
        db_table = "cymed_img_ai_triage_triage_queue"
        unique_together = [("tenant_id", "code")]

    def __str__(self) -> str:
        return f"{self.code} ({self.modality})"


class InferenceRun(BaseModel):
    class Status(models.TextChoices):
        QUEUED = "queued", "Queued"
        DISPATCHED = "dispatched", "Dispatched"
        RUNNING = "running", "Running"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"
        CANCELLED = "cancelled", "Cancelled"

    tenant_id = models.UUIDField(db_index=True)
    model = models.ForeignKey(
        AiModel,
        on_delete=models.PROTECT,
        related_name="inference_runs",
    )
    study_instance_uid = models.CharField(max_length=128, db_index=True)
    ordered_by_profile_id = models.UUIDField(null=True, blank=True)
    status = models.CharField(
        max_length=32,
        choices=Status.choices,
        default=Status.QUEUED,
    )
    requested_at = models.DateTimeField(default=timezone.now)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    latency_ms = models.IntegerField(default=0)
    error_message = models.TextField(blank=True)
    raw_response = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "cymed_img_ai_triage_inference_run"

    def __str__(self) -> str:
        return f"InferenceRun({self.study_instance_uid}, {self.status})"


class TriageFinding(BaseModel):
    class Severity(models.TextChoices):
        NORMAL = "normal", "Normal"
        LOW = "low", "Low"
        MODERATE = "moderate", "Moderate"
        HIGH = "high", "High"
        CRITICAL = "critical", "Critical"

    run = models.ForeignKey(
        InferenceRun,
        on_delete=models.CASCADE,
        related_name="findings",
    )
    finding_kind = models.CharField(max_length=64)
    severity = models.CharField(
        max_length=32,
        choices=Severity.choices,
        default=Severity.NORMAL,
    )
    confidence = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        default=Decimal("0"),
    )
    bbox = models.JSONField(default=dict, blank=True)
    raw = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "cymed_img_ai_triage_triage_finding"

    def __str__(self) -> str:
        return f"TriageFinding({self.finding_kind}, {self.severity})"


class TriageAlert(BaseModel):
    class Priority(models.TextChoices):
        CRITICAL = "critical", "Critical"
        URGENT = "urgent", "Urgent"
        ROUTINE = "routine", "Routine"

    class Status(models.TextChoices):
        OPEN = "open", "Open"
        ACKNOWLEDGED = "acknowledged", "Acknowledged"
        DISMISSED = "dismissed", "Dismissed"
        ESCALATED = "escalated", "Escalated"
        READ_BY_RADIOLOGIST = "read_by_radiologist", "Read by Radiologist"

    tenant_id = models.UUIDField(db_index=True)
    queue = models.ForeignKey(
        TriageQueue,
        on_delete=models.PROTECT,
        related_name="alerts",
    )
    run = models.ForeignKey(
        InferenceRun,
        on_delete=models.CASCADE,
        related_name="alerts",
    )
    study_instance_uid = models.CharField(max_length=128, db_index=True)
    patient_profile_id = models.UUIDField(null=True, blank=True)
    priority = models.CharField(
        max_length=32,
        choices=Priority.choices,
        default=Priority.ROUTINE,
    )
    finding_kind = models.CharField(max_length=64, blank=True)
    status = models.CharField(
        max_length=32,
        choices=Status.choices,
        default=Status.OPEN,
    )
    assigned_radiologist_id = models.UUIDField(null=True, blank=True)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    dismissed_reason = models.TextField(blank=True)

    class Meta:
        db_table = "cymed_img_ai_triage_triage_alert"

    def __str__(self) -> str:
        return f"TriageAlert({self.study_instance_uid}, {self.priority}, {self.status})"
