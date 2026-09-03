"""CyMed Pharmacy robotics business services."""
from __future__ import annotations

import uuid
from typing import Any, Optional, Tuple

from django.db import transaction
from django.utils import timezone


def _adapter_pyxis_dispense(*, device, order_id, drug_id, drug_name, qty) -> Tuple[bool, str, str]:
    return True, f"vendor-tracking-{uuid.uuid4()}", ""


def _adapter_omnicell_dispense(*, device, order_id, drug_id, drug_name, qty) -> Tuple[bool, str, str]:
    return True, f"vendor-tracking-{uuid.uuid4()}", ""


def _adapter_parata_dispense(*, device, order_id, drug_id, drug_name, qty) -> Tuple[bool, str, str]:
    return True, f"vendor-tracking-{uuid.uuid4()}", ""


def _adapter_meditech_dispense(*, device, order_id, drug_id, drug_name, qty) -> Tuple[bool, str, str]:
    return True, f"vendor-tracking-{uuid.uuid4()}", ""


def _adapter_kirby_lester_dispense(
    *, device, order_id, drug_id, drug_name, qty
) -> Tuple[bool, str, str]:
    return True, f"vendor-tracking-{uuid.uuid4()}", ""


def _adapter_generic_dispense(*, device, order_id, drug_id, drug_name, qty) -> Tuple[bool, str, str]:
    return True, f"vendor-tracking-{uuid.uuid4()}", ""


_ADAPTER_MAP = {
    "pyxis": _adapter_pyxis_dispense,
    "omnicell": _adapter_omnicell_dispense,
    "parata": _adapter_parata_dispense,
    "meditech": _adapter_meditech_dispense,
    "kirby_lester": _adapter_kirby_lester_dispense,
    "generic": _adapter_generic_dispense,
}


def heartbeat(*, device_id: Any, payload: Optional[dict] = None):
    from .models import RobotDevice, RobotEvent

    device = RobotDevice.objects.get(pk=device_id)
    now = timezone.now()
    device.last_heartbeat_at = now
    device.status = RobotDevice.Status.ONLINE
    device.save(update_fields=["last_heartbeat_at", "status", "updated_at"])
    RobotEvent.objects.create(
        device=device,
        at=now,
        kind=RobotEvent.Kind.HEARTBEAT,
        payload=payload or {},
    )
    return device


@transaction.atomic
def dispatch_dispense(
    *,
    device_id: Any,
    order_id: Any,
    drug_id: Any,
    drug_name: str,
    qty: int,
    patient_profile_id: Optional[Any] = None,
):
    from .models import DispenseJob, RobotDevice, RobotEvent

    device = RobotDevice.objects.select_for_update().get(pk=device_id)
    job = DispenseJob.objects.create(
        tenant_id=device.tenant_id,
        device=device,
        order_id=order_id,
        patient_profile_id=patient_profile_id,
        drug_id=drug_id,
        drug_name=drug_name,
        qty_requested=qty,
        status=DispenseJob.Status.DISPATCHED,
        dispatched_at=timezone.now(),
    )
    adapter = _ADAPTER_MAP.get(device.vendor, _adapter_generic_dispense)
    ok, vendor_reference, err = adapter(
        device=device,
        order_id=order_id,
        drug_id=drug_id,
        drug_name=drug_name,
        qty=qty,
    )
    if ok:
        job.vendor_reference = vendor_reference
        job.status = DispenseJob.Status.DISPENSING
        job.save(update_fields=["vendor_reference", "status", "updated_at"])
        RobotEvent.objects.create(
            device=device,
            kind=RobotEvent.Kind.DISPENSE_OK,
            payload={"job_id": str(job.pk), "vendor_reference": vendor_reference},
        )
    else:
        job.status = DispenseJob.Status.FAILED
        job.error_message = err
        job.save(update_fields=["status", "error_message", "updated_at"])
        RobotEvent.objects.create(
            device=device,
            kind=RobotEvent.Kind.DISPENSE_FAIL,
            payload={"job_id": str(job.pk), "error": err},
        )
    return job


@transaction.atomic
def mark_completed(
    *,
    job_id: Any,
    qty_dispensed: int,
    lot_number: str = "",
    vendor_reference: str = "",
):
    from .models import DispenseJob, RobotEvent

    job = DispenseJob.objects.select_for_update().get(pk=job_id)
    job.qty_dispensed = qty_dispensed
    job.status = DispenseJob.Status.COMPLETED
    if lot_number:
        job.lot_number = lot_number
    if vendor_reference:
        job.vendor_reference = vendor_reference
    job.completed_at = timezone.now()
    job.save(
        update_fields=[
            "qty_dispensed",
            "status",
            "lot_number",
            "vendor_reference",
            "completed_at",
            "updated_at",
        ]
    )
    RobotEvent.objects.create(
        device=job.device,
        kind=RobotEvent.Kind.DISPENSE_OK,
        payload={"job_id": str(job.pk), "qty_dispensed": qty_dispensed},
    )
    return job


@transaction.atomic
def mark_failed(*, job_id: Any, error_message: str):
    from .models import DispenseJob, RobotEvent

    job = DispenseJob.objects.select_for_update().get(pk=job_id)
    job.status = DispenseJob.Status.FAILED
    job.error_message = error_message
    job.completed_at = timezone.now()
    job.save(update_fields=["status", "error_message", "completed_at", "updated_at"])
    RobotEvent.objects.create(
        device=job.device,
        kind=RobotEvent.Kind.DISPENSE_FAIL,
        payload={"job_id": str(job.pk), "error": error_message},
    )
    return job


@transaction.atomic
def restock(
    *,
    device_id: Any,
    bin_code: str,
    drug_id: Any,
    drug_name: str,
    qty: int,
    lot_number: str = "",
    expiry_date: Any = None,
):
    from .models import RobotBinInventory, RobotDevice, RobotEvent

    device = RobotDevice.objects.get(pk=device_id)
    bin_row, created = RobotBinInventory.objects.select_for_update().get_or_create(
        device=device,
        bin_code=bin_code,
        defaults={
            "drug_id": drug_id,
            "drug_name": drug_name,
            "qty_on_hand": 0,
        },
    )
    bin_row.drug_id = drug_id
    bin_row.drug_name = drug_name
    bin_row.qty_on_hand = (bin_row.qty_on_hand or 0) + qty
    if lot_number:
        bin_row.lot_number = lot_number
    if expiry_date:
        bin_row.expiry_date = expiry_date
    bin_row.last_counted_at = timezone.now()
    bin_row.save()
    RobotEvent.objects.create(
        device=device,
        kind=RobotEvent.Kind.RESTOCK,
        payload={
            "bin_code": bin_code,
            "drug_name": drug_name,
            "qty_added": qty,
            "lot_number": lot_number,
        },
    )
    return bin_row


def lookup_bin(*, device_id: Any, drug_id: Any):
    from .models import RobotBinInventory

    if not drug_id:
        return None
    return (
        RobotBinInventory.objects.filter(device_id=device_id, drug_id=drug_id)
        .order_by("-qty_on_hand")
        .first()
    )
