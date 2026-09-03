"""Service functions for patient imaging results workflows."""
from __future__ import annotations

import secrets
from datetime import timedelta
from typing import Optional

from django.db import transaction
from django.utils import timezone

from .models import (
    ImageAccessGrant,
    ReportAcknowledgement,
    ReportDownload,
    ReportRelease,
)


@transaction.atomic
def release_report(
    *,
    tenant_id,
    patient_profile_id,
    study_instance_uid: str,
    report_id=None,
    released_by_profile_id=None,
    release_kind: str = "full",
    channels: Optional[list] = None,
    requires_counselling: bool = False,
    incidental_flag: bool = False,
) -> ReportRelease:
    release = ReportRelease.objects.create(
        tenant_id=tenant_id,
        patient_profile_id=patient_profile_id,
        study_instance_uid=study_instance_uid,
        report_id=report_id,
        release_kind=release_kind,
        status=ReportRelease.Status.RELEASED,
        released_by=released_by_profile_id,
        released_at=timezone.now(),
        delivery_channels=channels or [],
        requires_counselling=requires_counselling,
        incidental_findings_flag=incidental_flag,
    )
    return release


@transaction.atomic
def retract(*, release_id, reason: str) -> ReportRelease:
    release = ReportRelease.objects.get(pk=release_id)
    release.status = ReportRelease.Status.RETRACTED
    release.hold_reason = reason
    release.save(update_fields=["status", "hold_reason", "updated_at"] if hasattr(release, "updated_at") else ["status", "hold_reason"])
    return release


@transaction.atomic
def create_viewer_link(
    *,
    release_id,
    kind: str = "viewer_link",
    expires_in_hours: int = 72,
    max_downloads: int = -1,
) -> ImageAccessGrant:
    release = ReportRelease.objects.get(pk=release_id)
    access_token = secrets.token_urlsafe(32)
    url = f"/imaging/viewer/{access_token}"
    grant = ImageAccessGrant.objects.create(
        release=release,
        kind=kind,
        url=url,
        expires_at=timezone.now() + timedelta(hours=expires_in_hours),
        max_downloads=max_downloads,
        download_count=0,
        access_token=access_token,
    )
    return grant


@transaction.atomic
def record_download(
    *,
    release_id,
    kind: str = "pdf",
    downloaded_by_profile_id=None,
    ip_address: str = "",
) -> ReportDownload:
    release = ReportRelease.objects.get(pk=release_id)
    dl = ReportDownload.objects.create(
        release=release,
        kind=kind,
        downloaded_by_profile_id=downloaded_by_profile_id,
        ip_address=ip_address,
        at=timezone.now(),
    )
    grant = ImageAccessGrant.objects.filter(release=release).order_by("-created_at" if hasattr(ImageAccessGrant, "created_at") else "-id").first()
    if grant is not None:
        grant.download_count = grant.download_count + 1
        grant.save(update_fields=["download_count"])
    return dl


@transaction.atomic
def acknowledge(
    *,
    release_id,
    patient_profile_id,
    question_asked: str = "",
) -> ReportAcknowledgement:
    release = ReportRelease.objects.get(pk=release_id)
    ack = ReportAcknowledgement.objects.create(
        release=release,
        patient_profile_id=patient_profile_id,
        acknowledged_at=timezone.now(),
        question_asked=question_asked,
    )
    return ack


def generate_pdf(*, release_id) -> bytes:
    return b"PDF_STUB"
