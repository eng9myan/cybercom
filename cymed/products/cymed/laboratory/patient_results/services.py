"""Service layer for patient results release, notification, and acknowledgement flows."""
from __future__ import annotations

import uuid
from typing import Optional

from django.db import transaction
from django.utils import timezone

from .models import (
    ResultAcknowledgement,
    ResultDownload,
    ResultNotification,
    ResultRelease,
)


@transaction.atomic
def release_result(
    *,
    tenant_id: uuid.UUID,
    order_id: Optional[uuid.UUID],
    result_id: Optional[uuid.UUID],
    patient_profile_id: uuid.UUID,
    released_by_profile_id: Optional[uuid.UUID],
    release_kind: str = "full",
    channels: Optional[list] = None,
    requires_counselling: bool = False,
    counselling_note: str = "",
) -> ResultRelease:
    release = ResultRelease.objects.create(
        tenant_id=tenant_id,
        patient_profile_id=patient_profile_id,
        order_id=order_id,
        result_id=result_id,
        release_kind=release_kind,
        status=ResultRelease.Status.RELEASED,
        released_by=released_by_profile_id,
        released_at=timezone.now(),
        delivery_channels=list(channels or []),
        requires_counselling=requires_counselling,
        counselling_note=counselling_note,
    )
    return release


@transaction.atomic
def retract_release(*, release_id: uuid.UUID, reason: str) -> ResultRelease:
    release = ResultRelease.objects.select_for_update().get(pk=release_id)
    release.status = ResultRelease.Status.RETRACTED
    release.hold_reason = reason
    release.save(update_fields=["status", "hold_reason", "updated_at"])
    return release


@transaction.atomic
def record_download(
    *,
    release_id: uuid.UUID,
    downloaded_by_profile_id: Optional[uuid.UUID],
    kind: str = "pdf",
    ip_address: str = "",
    user_agent: str = "",
) -> ResultDownload:
    release = ResultRelease.objects.get(pk=release_id)
    download = ResultDownload.objects.create(
        release=release,
        downloaded_by_profile_id=downloaded_by_profile_id,
        kind=kind,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    return download


@transaction.atomic
def notify_patient(
    *,
    release_id: uuid.UUID,
    channels: list[str],
    recipient_map: dict,
) -> list[ResultNotification]:
    release = ResultRelease.objects.get(pk=release_id)
    notifications: list[ResultNotification] = []
    for channel in channels:
        recipient = recipient_map.get(channel, "")
        if not recipient:
            continue
        notification = ResultNotification.objects.create(
            release=release,
            channel=channel,
            status=ResultNotification.Status.QUEUED,
            recipient=recipient,
        )
        notifications.append(notification)
    return notifications


@transaction.atomic
def acknowledge(
    *,
    release_id: uuid.UUID,
    patient_profile_id: uuid.UUID,
    question_asked: str = "",
) -> ResultAcknowledgement:
    release = ResultRelease.objects.get(pk=release_id)
    ack = ResultAcknowledgement.objects.create(
        release=release,
        patient_profile_id=patient_profile_id,
        question_asked=question_asked,
    )
    return ack


def generate_pdf(*, release_id: uuid.UUID) -> bytes:
    _ = ResultRelease.objects.get(pk=release_id)
    return b"PDF_STUB"
