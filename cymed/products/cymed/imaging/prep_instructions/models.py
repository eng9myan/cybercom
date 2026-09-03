"""Data models for modality-specific patient prep, checklists, and contrast consent."""
from __future__ import annotations

import uuid
from decimal import Decimal

from django.db import models
from django.utils import timezone

from platform.common.models import BaseModel


class PrepTemplate(BaseModel):
    class Modality(models.TextChoices):
        XRAY = "xray", "X-Ray"
        CT = "ct", "CT"
        MRI = "mri", "MRI"
        US = "us", "Ultrasound"
        MAMMO = "mammo", "Mammography"
        NM = "nm", "Nuclear Medicine"
        PET = "pet", "PET"
        FLUORO = "fluoro", "Fluoroscopy"
        OTHER = "other", "Other"

    tenant_id = models.UUIDField(null=True, blank=True, db_index=True)
    code = models.CharField(max_length=64)
    title = models.CharField(max_length=255)
    title_ar = models.CharField(max_length=255, blank=True)
    modality = models.CharField(max_length=32, choices=Modality.choices)
    body_part = models.CharField(max_length=64, blank=True)
    contrast_involved = models.BooleanField(default=False)
    fasting_required = models.BooleanField(default=False)
    fasting_hours = models.IntegerField(default=0)
    hydration_required = models.BooleanField(default=False)
    medications_to_hold = models.JSONField(default=list, blank=True)
    clothing_instructions = models.TextField(blank=True)
    arrive_minutes_before = models.IntegerField(default=15)
    what_to_bring = models.JSONField(default=list, blank=True)
    body_html = models.TextField(blank=True)
    body_html_ar = models.TextField(blank=True)
    version = models.IntegerField(default=1)
    active = models.BooleanField(default=True)

    class Meta:
        db_table = "cymed_img_prep_instructions_prep_template"
        unique_together = [("tenant_id", "code", "version")]

    def __str__(self) -> str:
        return f"{self.code} v{self.version} - {self.title}"


class PrepAssignment(BaseModel):
    class Status(models.TextChoices):
        ASSIGNED = "assigned", "Assigned"
        VIEWED = "viewed", "Viewed"
        CONFIRMED = "confirmed", "Confirmed"
        PARTIAL = "partial", "Partial"
        NOT_READY = "not_ready", "Not Ready"

    tenant_id = models.UUIDField(db_index=True)
    patient_profile_id = models.UUIDField(db_index=True)
    booking_id = models.UUIDField(null=True, blank=True)
    template = models.ForeignKey(
        PrepTemplate,
        on_delete=models.PROTECT,
        related_name="assignments",
    )
    status = models.CharField(
        max_length=32,
        choices=Status.choices,
        default=Status.ASSIGNED,
    )
    viewed_at = models.DateTimeField(null=True, blank=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    language = models.CharField(max_length=8, default="en")

    class Meta:
        db_table = "cymed_img_prep_instructions_prep_assignment"

    def __str__(self) -> str:
        return f"PrepAssignment {self.pk} - {self.status}"


class PrepChecklistItem(BaseModel):
    class ItemKind(models.TextChoices):
        FASTING = "fasting", "Fasting"
        HYDRATION = "hydration", "Hydration"
        HOLD_MEDICATION = "hold_medication", "Hold Medication"
        BRING_ITEM = "bring_item", "Bring Item"
        ARRIVAL_TIME = "arrival_time", "Arrival Time"
        CLOTHING = "clothing", "Clothing"
        CONSENT = "consent", "Consent"
        OTHER = "other", "Other"

    assignment = models.ForeignKey(
        PrepAssignment,
        on_delete=models.CASCADE,
        related_name="items",
    )
    position = models.IntegerField(default=0)
    label = models.CharField(max_length=255)
    label_ar = models.CharField(max_length=255, blank=True)
    item_kind = models.CharField(
        max_length=32,
        choices=ItemKind.choices,
        default=ItemKind.OTHER,
    )
    required = models.BooleanField(default=True)
    checked = models.BooleanField(default=False)
    checked_at = models.DateTimeField(null=True, blank=True)
    note = models.TextField(blank=True)

    class Meta:
        db_table = "cymed_img_prep_instructions_prep_checklist_item"
        ordering = ["position", "id"]

    def __str__(self) -> str:
        return f"{self.item_kind}:{self.label}"


class ContrastConsent(BaseModel):
    class ContrastKind(models.TextChoices):
        IODINATED = "iodinated", "Iodinated"
        GADOLINIUM = "gadolinium", "Gadolinium"
        BARIUM = "barium", "Barium"
        MICROBUBBLE = "microbubble", "Microbubble"

    class PregnancyStatus(models.TextChoices):
        UNKNOWN = "unknown", "Unknown"
        NOT_PREGNANT = "not_pregnant", "Not Pregnant"
        PREGNANT = "pregnant", "Pregnant"
        NA = "na", "N/A"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        SIGNED = "signed", "Signed"
        DECLINED = "declined", "Declined"
        EXPIRED = "expired", "Expired"

    tenant_id = models.UUIDField(db_index=True)
    patient_profile_id = models.UUIDField(db_index=True)
    assignment = models.ForeignKey(
        PrepAssignment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="contrast_consents",
    )
    contrast_kind = models.CharField(max_length=32, choices=ContrastKind.choices)
    allergies_reviewed = models.BooleanField(default=False)
    egfr_verified = models.BooleanField(default=False)
    egfr_value = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
    )
    pregnancy_status = models.CharField(
        max_length=32,
        choices=PregnancyStatus.choices,
        default=PregnancyStatus.UNKNOWN,
    )
    consent_signed_at = models.DateTimeField(null=True, blank=True)
    signature_url = models.URLField(blank=True)
    witness_profile_id = models.UUIDField(null=True, blank=True)
    status = models.CharField(
        max_length=32,
        choices=Status.choices,
        default=Status.PENDING,
    )
    decline_reason = models.TextField(blank=True)

    class Meta:
        db_table = "cymed_img_prep_instructions_contrast_consent"

    def __str__(self) -> str:
        return f"ContrastConsent {self.pk} - {self.contrast_kind}/{self.status}"
