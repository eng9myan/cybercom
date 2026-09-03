"""Service functions for CyMed Laboratory courier tracking flows."""

from __future__ import annotations

from decimal import Decimal
from typing import Optional
from uuid import UUID

from django.db import transaction
from django.utils import timezone

from .models import ChainOfCustodyEvent, Manifest, Route, Run, TransportTemperature


REFRIGERATED_MIN_C = Decimal("2")
REFRIGERATED_MAX_C = Decimal("8")
FROZEN_MAX_C = Decimal("-70")


@transaction.atomic
def open_run(
    *,
    tenant_id: UUID,
    route_id: UUID,
    run_date,
    driver_id: Optional[UUID] = None,
    vehicle_plate: str = "",
    cold_chain: bool = False,
) -> Run:
    route = Route.objects.get(pk=route_id, tenant_id=tenant_id)
    run = Run.objects.create(
        tenant_id=tenant_id,
        route=route,
        run_date=run_date,
        driver_id=driver_id,
        vehicle_plate=vehicle_plate,
        status=Run.Status.IN_PROGRESS,
        started_at=timezone.now(),
        cold_chain=cold_chain,
    )
    return run


@transaction.atomic
def close_run(*, run_id: UUID) -> Run:
    run = Run.objects.select_for_update().get(pk=run_id)
    run.status = Run.Status.COMPLETED
    run.completed_at = timezone.now()
    run.save(update_fields=["status", "completed_at", "updated_at"])
    return run


@transaction.atomic
def record_custody(
    *,
    tenant_id: UUID,
    specimen_barcode: str,
    kind: str,
    order_id: Optional[UUID] = None,
    run_id: Optional[UUID] = None,
    actor_profile_id: Optional[UUID] = None,
    lat: Optional[Decimal] = None,
    lng: Optional[Decimal] = None,
    temperature_c: Optional[Decimal] = None,
    signature_url: str = "",
    note: str = "",
) -> ChainOfCustodyEvent:
    run = None
    if run_id is not None:
        run = Run.objects.get(pk=run_id)
    event = ChainOfCustodyEvent.objects.create(
        tenant_id=tenant_id,
        specimen_barcode=specimen_barcode,
        order_id=order_id,
        run=run,
        at=timezone.now(),
        kind=kind,
        actor_profile_id=actor_profile_id,
        lat=lat,
        lng=lng,
        temperature_c=temperature_c,
        signature_url=signature_url,
        note=note,
    )
    return event


@transaction.atomic
def record_temperature(
    *,
    run_id: UUID,
    specimen_barcode: str,
    temperature_c: Decimal,
    cold_chain_kind: str = "refrigerated",
) -> TransportTemperature:
    run = Run.objects.get(pk=run_id)
    temp = Decimal(temperature_c)
    breach = False
    if cold_chain_kind == "refrigerated":
        if temp < REFRIGERATED_MIN_C or temp > REFRIGERATED_MAX_C:
            breach = True
    elif cold_chain_kind == "frozen":
        if temp > FROZEN_MAX_C:
            breach = True
    reading = TransportTemperature.objects.create(
        run=run,
        specimen_barcode=specimen_barcode,
        at=timezone.now(),
        temperature_c=temp,
        breach=breach,
    )
    return reading


@transaction.atomic
def generate_manifest(*, run_id: UUID, specimen_barcodes: list[str]) -> Manifest:
    run = Run.objects.get(pk=run_id)
    barcodes = list(specimen_barcodes or [])
    manifest = Manifest.objects.create(
        tenant_id=run.tenant_id,
        run=run,
        generated_at=timezone.now(),
        specimen_barcodes=barcodes,
        total_specimens=len(barcodes),
    )
    return manifest


@transaction.atomic
def deliver_manifest(*, manifest_id: UUID, receiver_signature_url: str) -> Manifest:
    manifest = Manifest.objects.select_for_update().get(pk=manifest_id)
    manifest.receiver_signature_url = receiver_signature_url
    manifest.delivered_at = timezone.now()
    manifest.save(update_fields=["receiver_signature_url", "delivered_at", "updated_at"])
    return manifest


def locate_specimen(*, specimen_barcode: str) -> list[ChainOfCustodyEvent]:
    return list(
        ChainOfCustodyEvent.objects.filter(specimen_barcode=specimen_barcode).order_by("at")
    )
