"""Domain models for patient-facing laboratory result delivery."""
from __future__ import annotations

import uuid
from decimal import Decimal

from django.db import models
from django.utils import timezone

from platform.common.fields import EncryptedText
from platform.common.models import BaseModel


class ResultRelease(BaseModel):
    class ReleaseKind(models.TextChoices):
        FULL = "full", "Full"
        REDACTED = "redacted", "Redacted"
        PRELIMINARY = "preliminary", "Preliminary"
        AMENDED = "amended", "Amended"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        RELEASED = "released", "Released"
        RETRACTED = "retracted", "Retracted"
        HELD_FOR_REVIEW = "held_for_review", "Held for Review"

    tenant_id = models.UUIDField(db_index=True)
    patient_profile_id = models.UUIDField(db_index=True)
    order_id = models.UUIDField(null=True, blank=True)
    result_id = models.UUIDField(null=True, blank=True)
    release_kind = models.CharField(max_length=32, choices=ReleaseKind.choices, default=ReleaseKind.FULL)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.PENDING)
    released_by = models.UUIDField(null=True, blank=True)
    released_at = models.DateTimeField(null=True, blank=True)
    hold_reason = models.TextField(blank=True)
    delivery_channels = models.JSONField(default=list, blank=True)
    requires_counselling = models.BooleanField(default=False)
    counselling_note = EncryptedText(classification="phi")

    class Meta:
        db_table = "cymed_lab_patient_results_result_release"

    def __str__(self) -> str:
        return f"ResultRelease({self.pk}, {self.status})"


class ResultDownload(BaseModel):
    class Kind(models.TextChoices):
        PDF = "pdf", "PDF"
        JSON = "json", "JSON"
        HL7 = "hl7", "HL7"
        FHIR = "fhir", "FHIR"

    release = models.ForeignKey(ResultRelease, on_delete=models.CASCADE, related_name="downloads")
    downloaded_by_profile_id = models.UUIDField(null=True, blank=True)
    ip_address = models.CharField(max_length=64, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)
    kind = models.CharField(max_length=32, choices=Kind.choices, default=Kind.PDF)
    at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "cymed_lab_patient_results_result_download"

    def __str__(self) -> str:
        return f"ResultDownload({self.pk}, {self.kind})"


class ResultNotification(BaseModel):
    class Channel(models.TextChoices):
        EMAIL = "email", "Email"
        SMS = "sms", "SMS"
        WHATSAPP = "whatsapp", "WhatsApp"
        PUSH = "push", "Push"

    class Status(models.TextChoices):
        QUEUED = "queued", "Queued"
        SENT = "sent", "Sent"
        DELIVERED = "delivered", "Delivered"
        FAILED = "failed", "Failed"
        OPENED = "opened", "Opened"

    release = models.ForeignKey(ResultRelease, on_delete=models.CASCADE, related_name="notifications")
    channel = models.CharField(max_length=32, choices=Channel.choices)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.QUEUED)
    recipient = models.CharField(max_length=255)
    provider_reference = models.CharField(max_length=128, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)

    class Meta:
        db_table = "cymed_lab_patient_results_result_notification"

    def __str__(self) -> str:
        return f"ResultNotification({self.pk}, {self.channel}, {self.status})"


class ResultAcknowledgement(BaseModel):
    release = models.ForeignKey(ResultRelease, on_delete=models.CASCADE, related_name="acknowledgements")
    patient_profile_id = models.UUIDField(db_index=True)
    acknowledged_at = models.DateTimeField(default=timezone.now)
    question_asked = EncryptedText(classification="phi")

    class Meta:
        db_table = "cymed_lab_patient_results_result_acknowledgement"

    def __str__(self) -> str:
        return f"ResultAcknowledgement({self.pk}, patient={self.patient_profile_id})"
