"""Business services for the image_sharing sub-app."""
from __future__ import annotations

import secrets
from datetime import timedelta
from decimal import Decimal
from typing import Any, Optional

from django.contrib.auth.hashers import check_password, make_password
from django.db import transaction
from django.utils import timezone

from .models import ExternalImport, ShareAccessLog, ShareableStudy, ShareLink


@transaction.atomic
def index_study(
    *,
    tenant_id: Any,
    patient_profile_id: Any,
    study_instance_uid: str,
    modality: str = "",
    study_date: Any = None,
    description: str = "",
    original_facility_id: Any = None,
    size_mb: Any = 0,
    image_count: int = 0,
    series_count: int = 0,
) -> ShareableStudy:
    study, _created = ShareableStudy.objects.update_or_create(
        tenant_id=tenant_id,
        study_instance_uid=study_instance_uid,
        defaults={
            "patient_profile_id": patient_profile_id,
            "modality": modality,
            "study_date": study_date,
            "description": description,
            "original_facility_id": original_facility_id,
            "size_mb": Decimal(str(size_mb)),
            "image_count": int(image_count),
            "series_count": int(series_count),
        },
    )
    return study


@transaction.atomic
def create_share_link(
    *,
    tenant_id: Any,
    shareable_study_id: Any,
    created_by_profile_id: Any,
    recipient_kind: str,
    recipient_email: str = "",
    recipient_name: str = "",
    recipient_organization: str = "",
    expires_in_hours: int = 168,
    max_views: int = -1,
    passphrase: str = "",
    download_enabled: bool = True,
    watermark_text: str = "",
) -> ShareLink:
    study = ShareableStudy.objects.get(pk=shareable_study_id)
    token = secrets.token_urlsafe(32)[:64]
    passphrase_hash = make_password(passphrase) if passphrase else ""
    expires_at: Optional[Any] = None
    if expires_in_hours and int(expires_in_hours) > 0:
        expires_at = timezone.now() + timedelta(hours=int(expires_in_hours))
    link = ShareLink.objects.create(
        tenant_id=tenant_id,
        shareable_study=study,
        created_by_profile_id=created_by_profile_id,
        recipient_kind=recipient_kind,
        recipient_email=recipient_email,
        recipient_name=recipient_name,
        recipient_organization=recipient_organization,
        token=token,
        passphrase_hash=passphrase_hash,
        expires_at=expires_at,
        max_views=int(max_views),
        view_count=0,
        download_enabled=bool(download_enabled),
        watermark_text=watermark_text,
        status=ShareLink.Status.ACTIVE,
    )
    return link


@transaction.atomic
def open_link(
    *,
    token: str,
    passphrase: str = "",
    ip_address: str = "",
    user_agent: str = "",
) -> ShareLink:
    link = ShareLink.objects.select_for_update().get(token=token)
    now = timezone.now()

    if link.status != ShareLink.Status.ACTIVE:
        ShareAccessLog.objects.create(
            link=link,
            ip_address=ip_address,
            user_agent=user_agent,
            action=ShareAccessLog.Action.EXPIRED,
            note=f"link status={link.status}",
        )
        raise ValueError(f"share link not active (status={link.status})")

    if link.expires_at and link.expires_at <= now:
        link.status = ShareLink.Status.EXPIRED
        link.save(update_fields=["status"])
        ShareAccessLog.objects.create(
            link=link,
            ip_address=ip_address,
            user_agent=user_agent,
            action=ShareAccessLog.Action.EXPIRED,
            note="expired at open",
        )
        raise ValueError("share link expired")

    if link.passphrase_hash:
        if not passphrase or not check_password(passphrase, link.passphrase_hash):
            ShareAccessLog.objects.create(
                link=link,
                ip_address=ip_address,
                user_agent=user_agent,
                action=ShareAccessLog.Action.PASSPHRASE_FAILED,
                note="wrong passphrase",
            )
            raise ValueError("invalid passphrase")

    link.view_count = int(link.view_count) + 1
    ShareAccessLog.objects.create(
        link=link,
        ip_address=ip_address,
        user_agent=user_agent,
        action=ShareAccessLog.Action.OPENED,
        note="",
    )
    ShareAccessLog.objects.create(
        link=link,
        ip_address=ip_address,
        user_agent=user_agent,
        action=ShareAccessLog.Action.VIEWED,
        note="",
    )

    if link.max_views is not None and link.max_views >= 0 and link.view_count >= link.max_views:
        link.status = ShareLink.Status.USED_UP

    link.save(update_fields=["view_count", "status"])
    return link


@transaction.atomic
def record_download(
    *,
    token: str,
    ip_address: str = "",
    user_agent: str = "",
) -> ShareAccessLog:
    link = ShareLink.objects.select_for_update().get(token=token)
    if not link.download_enabled:
        raise ValueError("downloads disabled for this share link")
    if link.status != ShareLink.Status.ACTIVE:
        raise ValueError(f"share link not active (status={link.status})")
    log = ShareAccessLog.objects.create(
        link=link,
        ip_address=ip_address,
        user_agent=user_agent,
        action=ShareAccessLog.Action.DOWNLOADED,
        note="",
    )
    return log


@transaction.atomic
def revoke_link(*, link_id: Any, reason: str) -> ShareLink:
    link = ShareLink.objects.select_for_update().get(pk=link_id)
    link.status = ShareLink.Status.REVOKED
    link.save(update_fields=["status"])
    ShareAccessLog.objects.create(
        link=link,
        action=ShareAccessLog.Action.EXPIRED,
        note=f"revoked: {reason}",
    )
    return link


@transaction.atomic
def import_external_study(
    *,
    tenant_id: Any,
    patient_profile_id: Any = None,
    source_kind: str = "cd",
    original_facility_name: str = "",
    size_mb: Any = 0,
    image_count: int = 0,
    imported_by_profile_id: Any = None,
    study_instance_uid: str = "",
) -> ExternalImport:
    record = ExternalImport.objects.create(
        tenant_id=tenant_id,
        patient_profile_id=patient_profile_id,
        source_kind=source_kind,
        original_facility_name=original_facility_name,
        size_mb=Decimal(str(size_mb)),
        image_count=int(image_count),
        imported_at=timezone.now(),
        imported_by_profile_id=imported_by_profile_id,
        study_instance_uid=study_instance_uid,
        status=ExternalImport.Status.UPLOADED,
    )
    return record
