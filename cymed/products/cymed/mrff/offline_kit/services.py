"""Service functions for CyMed MRFF offline_kit sub-app."""
from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any

from django.db import transaction
from django.utils import timezone

from .models import (
    ConflictResolution,
    OfflineCdssRun,
    OfflineDevice,
    OfflineIntake,
    SyncQueueItem,
)


def _apply_server(payload_kind: str, payload: dict) -> tuple[bool, uuid.UUID]:
    return (True, uuid.uuid4())


@transaction.atomic
def register_device(
    *,
    tenant_id,
    device_uuid: str,
    device_kind: str,
    operator_profile_id=None,
    facility_id=None,
    accho_flag: bool = False,
    app_version: str = "",
    platform: str = "",
) -> OfflineDevice:
    device, _created = OfflineDevice.objects.update_or_create(
        device_uuid=device_uuid,
        defaults={
            "tenant_id": tenant_id,
            "device_kind": device_kind,
            "operator_profile_id": operator_profile_id,
            "facility_id": facility_id,
            "accho_flag": accho_flag,
            "app_version": app_version,
            "platform": platform,
            "active": True,
        },
    )
    return device


@transaction.atomic
def capture_intake(
    *,
    tenant_id,
    device_id,
    local_id: str,
    patient_snapshot: dict,
    chief_complaint: str = "",
    vitals: dict | None = None,
    history: list | None = None,
    encounter_kind: str = "routine",
    accho_specific: dict | None = None,
) -> OfflineIntake:
    device = OfflineDevice.objects.get(pk=device_id)
    intake = OfflineIntake.objects.create(
        tenant_id=tenant_id,
        device=device,
        local_id=local_id,
        patient_snapshot=patient_snapshot or {},
        chief_complaint=chief_complaint,
        vitals=vitals or {},
        history=history or [],
        encounter_kind=encounter_kind,
        accho_specific=accho_specific or {},
        sync_status=OfflineIntake.SyncStatus.PENDING,
    )
    return intake


@transaction.atomic
def enqueue_payload(
    *,
    tenant_id,
    device_id,
    payload_kind: str,
    local_ref: str,
    payload: dict,
) -> SyncQueueItem:
    device = OfflineDevice.objects.get(pk=device_id)
    item = SyncQueueItem.objects.create(
        tenant_id=tenant_id,
        device=device,
        payload_kind=payload_kind,
        local_ref=local_ref,
        payload=payload or {},
        status=SyncQueueItem.Status.QUEUED,
    )
    return item


@transaction.atomic
def sync_next_batch(*, device_id, limit: int = 50) -> dict[str, int]:
    counters = {"sent": 0, "conflict": 0, "failed": 0}
    items = list(
        SyncQueueItem.objects.filter(
            device_id=device_id,
            status=SyncQueueItem.Status.QUEUED,
        ).order_by("created_at")[:limit]
    )
    for item in items:
        item.status = SyncQueueItem.Status.IN_PROGRESS
        item.attempted_at = timezone.now()
        item.attempts = (item.attempts or 0) + 1
        item.save(update_fields=["status", "attempted_at", "attempts"])
        try:
            success, server_id = _apply_server(item.payload_kind, item.payload)
        except Exception as exc:  # noqa: BLE001
            item.status = SyncQueueItem.Status.FAILED
            item.error_message = str(exc)
            item.save(update_fields=["status", "error_message"])
            counters["failed"] += 1
            continue
        if success:
            item.status = SyncQueueItem.Status.SENT
            item.server_id = server_id
            item.error_message = ""
            item.save(update_fields=["status", "server_id", "error_message"])
            counters["sent"] += 1
        else:
            item.status = SyncQueueItem.Status.CONFLICT
            item.save(update_fields=["status"])
            ConflictResolution.objects.create(
                queue_item=item,
                server_snapshot={},
                client_snapshot=item.payload,
                strategy=ConflictResolution.Strategy.MANUAL,
            )
            counters["conflict"] += 1
    return counters


@transaction.atomic
def resolve_conflict(
    *,
    resolution_id,
    strategy: str,
    resolved_payload: dict | None = None,
    resolved_by_profile_id=None,
) -> ConflictResolution:
    resolution = ConflictResolution.objects.select_related("queue_item").get(pk=resolution_id)
    resolution.strategy = strategy
    resolution.resolved_payload = resolved_payload or {}
    resolution.resolved_by_profile_id = resolved_by_profile_id
    resolution.resolved_at = timezone.now()
    resolution.save(
        update_fields=[
            "strategy",
            "resolved_payload",
            "resolved_by_profile_id",
            "resolved_at",
        ]
    )
    queue_item = resolution.queue_item
    if strategy in (
        ConflictResolution.Strategy.SERVER_WINS,
        ConflictResolution.Strategy.CLIENT_WINS,
        ConflictResolution.Strategy.MERGE,
    ):
        queue_item.status = SyncQueueItem.Status.SENT
        if not queue_item.server_id:
            queue_item.server_id = uuid.uuid4()
        queue_item.save(update_fields=["status", "server_id"])
    return resolution


@transaction.atomic
def record_offline_cdss(
    *,
    intake_id,
    kind: str,
    score: Any,
    band: str,
    recommendations: list | None = None,
) -> OfflineCdssRun:
    intake = OfflineIntake.objects.get(pk=intake_id)
    score_decimal = score if isinstance(score, Decimal) else Decimal(str(score))
    run = OfflineCdssRun.objects.create(
        intake=intake,
        kind=kind,
        score=score_decimal,
        band=band or OfflineCdssRun.Band.N_A,
        recommendations=recommendations or [],
    )
    alerts = list(intake.cdss_alerts or [])
    alerts.append({"kind": kind, "band": run.band, "score": str(score_decimal)})
    intake.cdss_alerts = alerts
    intake.save(update_fields=["cdss_alerts"])
    return run
