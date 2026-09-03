"""Models for secure digital DICOM sharing replacing physical CD/DVD delivery."""
from __future__ import annotations

import uuid
from decimal import Decimal

from django.db import models
from django.utils import timezone

from platform.common.models import BaseModel


class ShareableStudy(BaseModel):
    tenant_id = models.UUIDField(db_index=True)
    patient_profile_id = models.UUIDField(db_index=True)
    study_instance_uid = models.CharField(max_length=128, db_index=True)
    modality = models.CharField(max_length=32, blank=True)
    study_date = models.DateField(null=True, blank=True)
    description = models.CharField(max_length=255, blank=True)
    original_facility_id = models.UUIDField(null=True, blank=True)
    size_mb = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    image_count = models.IntegerField(default=0)
    series_count = models.IntegerField(default=0)

    class Meta:
        db_table = "cymed_img_image_sharing_shareable_study"

    def __str__(self) -> str:
        return f"ShareableStudy({self.study_instance_uid})"


class ShareLink(BaseModel):
    class RecipientKind(models.TextChoices):
        PATIENT = "patient", "Patient"
        PROVIDER = "provider", "Provider"
        EXTERNAL_RADIOLOGIST = "external_radiologist", "External Radiologist"
        INSURER = "insurer", "Insurer"
        LAWYER = "lawyer", "Lawyer"

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        EXPIRED = "expired", "Expired"
        REVOKED = "revoked", "Revoked"
        USED_UP = "used_up", "Used Up"

    tenant_id = models.UUIDField(db_index=True)
    shareable_study = models.ForeignKey(
        ShareableStudy,
        on_delete=models.CASCADE,
        related_name="share_links",
    )
    created_by_profile_id = models.UUIDField(null=True, blank=True)
    recipient_kind = models.CharField(max_length=32, choices=RecipientKind.choices)
    recipient_email = models.CharField(max_length=255, blank=True)
    recipient_name = models.CharField(max_length=255, blank=True)
    recipient_organization = models.CharField(max_length=255, blank=True)
    token = models.CharField(max_length=64, unique=True)
    passphrase_hash = models.CharField(max_length=128, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    max_views = models.IntegerField(default=-1)
    view_count = models.IntegerField(default=0)
    download_enabled = models.BooleanField(default=True)
    watermark_text = models.CharField(max_length=128, blank=True)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.ACTIVE)

    class Meta:
        db_table = "cymed_img_image_sharing_share_link"

    def __str__(self) -> str:
        return f"ShareLink({self.token[:12]}...)"


class ShareAccessLog(BaseModel):
    class Action(models.TextChoices):
        OPENED = "opened", "Opened"
        VIEWED = "viewed", "Viewed"
        DOWNLOADED = "downloaded", "Downloaded"
        PASSPHRASE_FAILED = "passphrase_failed", "Passphrase Failed"
        EXPIRED = "expired", "Expired"

    link = models.ForeignKey(
        ShareLink,
        on_delete=models.CASCADE,
        related_name="access_logs",
    )
    at = models.DateTimeField(default=timezone.now)
    ip_address = models.CharField(max_length=64, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)
    action = models.CharField(max_length=32, choices=Action.choices)
    note = models.TextField(blank=True)

    class Meta:
        db_table = "cymed_img_image_sharing_share_access_log"

    def __str__(self) -> str:
        return f"ShareAccessLog({self.action}@{self.at:%Y-%m-%d %H:%M:%S})"


class ExternalImport(BaseModel):
    class SourceKind(models.TextChoices):
        CD = "cd", "CD"
        DVD = "dvd", "DVD"
        USB = "usb", "USB"
        IMPORT_LINK = "import_link", "Import Link"
        DICOM_WEB = "dicom_web", "DICOMweb"
        EMAIL = "email", "Email"

    class Status(models.TextChoices):
        UPLOADED = "uploaded", "Uploaded"
        ANONYMISED = "anonymised", "Anonymised"
        MERGED = "merged", "Merged"
        REJECTED = "rejected", "Rejected"

    tenant_id = models.UUIDField(db_index=True)
    patient_profile_id = models.UUIDField(null=True, blank=True, db_index=True)
    source_kind = models.CharField(max_length=32, choices=SourceKind.choices, default=SourceKind.CD)
    original_facility_name = models.CharField(max_length=255, blank=True)
    size_mb = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    image_count = models.IntegerField(default=0)
    imported_at = models.DateTimeField(default=timezone.now)
    imported_by_profile_id = models.UUIDField(null=True, blank=True)
    study_instance_uid = models.CharField(max_length=128, blank=True, db_index=True)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.UPLOADED)

    class Meta:
        db_table = "cymed_img_image_sharing_external_import"

    def __str__(self) -> str:
        return f"ExternalImport({self.source_kind}:{self.study_instance_uid or self.id})"
