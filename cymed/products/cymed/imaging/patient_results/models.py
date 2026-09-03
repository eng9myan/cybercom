"""Models for direct patient access to imaging reports and images."""
from __future__ import annotations

import uuid
from decimal import Decimal

from django.db import models
from django.utils import timezone

from platform.common.models import BaseModel


class ReportRelease(BaseModel):
    class ReleaseKind(models.TextChoices):
        FULL = "full", "Full"
        PRELIMINARY = "preliminary", "Preliminary"
        AMENDED = "amended", "Amended"
        REDACTED = "redacted", "Redacted"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        RELEASED = "released", "Released"
        RETRACTED = "retracted", "Retracted"
        HELD_FOR_REVIEW = "held_for_review", "Held For Review"

    tenant_id = models.UUIDField(db_index=True)
    patient_profile_id = models.UUIDField(db_index=True)
    study_instance_uid = models.CharField(max_length=128, db_index=True)
    report_id = models.UUIDField(null=True, blank=True)
    release_kind = models.CharField(
        max_length=32,
        choices=ReleaseKind.choices,
        default=ReleaseKind.FULL,
    )
    status = models.CharField(
        max_length=32,
        choices=Status.choices,
        default=Status.PENDING,
    )
    released_by = models.UUIDField(null=True, blank=True)
    released_at = models.DateTimeField(null=True, blank=True)
    hold_reason = models.TextField(blank=True)
    delivery_channels = models.JSONField(default=list, blank=True)
    requires_counselling = models.BooleanField(default=False)
    incidental_findings_flag = models.BooleanField(default=False)

    class Meta:
        db_table = "cymed_img_patient_results_report_release"

    def __str__(self) -> str:
        return f"ReportRelease({self.study_instance_uid}, {self.status})"


class ImageAccessGrant(BaseModel):
    class Kind(models.TextChoices):
        VIEWER_LINK = "viewer_link", "Viewer Link"
        DOWNLOAD_ZIP = "download_zip", "Download Zip"
        DICOM_WEB = "dicom_web", "DICOM Web"

    release = models.ForeignKey(
        ReportRelease,
        on_delete=models.CASCADE,
        related_name="access_grants",
    )
    kind = models.CharField(
        max_length=32,
        choices=Kind.choices,
        default=Kind.VIEWER_LINK,
    )
    url = models.URLField(blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    max_downloads = models.IntegerField(default=-1)
    download_count = models.IntegerField(default=0)
    access_token = models.CharField(max_length=64, blank=True)

    class Meta:
        db_table = "cymed_img_patient_results_image_access_grant"

    def __str__(self) -> str:
        return f"ImageAccessGrant({self.kind}, {self.access_token})"


class ReportDownload(BaseModel):
    class Kind(models.TextChoices):
        PDF = "pdf", "PDF"
        DICOM_SR = "dicom_sr", "DICOM SR"
        CDA = "cda", "CDA"
        FHIR = "fhir", "FHIR"

    release = models.ForeignKey(
        ReportRelease,
        on_delete=models.CASCADE,
        related_name="downloads",
    )
    kind = models.CharField(
        max_length=32,
        choices=Kind.choices,
        default=Kind.PDF,
    )
    downloaded_by_profile_id = models.UUIDField(null=True, blank=True)
    ip_address = models.CharField(max_length=64, blank=True)
    at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "cymed_img_patient_results_report_download"

    def __str__(self) -> str:
        return f"ReportDownload({self.kind}, {self.at})"


class ReportAcknowledgement(BaseModel):
    release = models.ForeignKey(
        ReportRelease,
        on_delete=models.CASCADE,
        related_name="acknowledgements",
    )
    patient_profile_id = models.UUIDField(db_index=True)
    acknowledged_at = models.DateTimeField(default=timezone.now)
    question_asked = models.TextField(blank=True)

    class Meta:
        db_table = "cymed_img_patient_results_report_acknowledgement"

    def __str__(self) -> str:
        return f"ReportAcknowledgement({self.patient_profile_id}, {self.acknowledged_at})"
