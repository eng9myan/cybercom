"""CyMed Pharmacy Compounding business logic."""
from __future__ import annotations

from datetime import timedelta
from typing import Any, Optional
from uuid import UUID

from django.db import transaction
from django.utils import timezone


_DEFAULT_STEPS_BY_KIND: dict[str, list[str]] = {
    "sterile": [
        "hand_hygiene",
        "gowning",
        "gather",
        "calc",
        "measure",
        "mix",
        "fill",
        "label",
        "qa_visual",
        "qa_gc",
        "release",
    ],
    "iv_admixture": [
        "hand_hygiene",
        "gowning",
        "gather",
        "calc",
        "measure",
        "mix",
        "fill",
        "label",
        "qa_visual",
        "release",
    ],
    "tpn": [
        "hand_hygiene",
        "gowning",
        "gather",
        "calc",
        "measure",
        "mix",
        "fill",
        "label",
        "qa_visual",
        "qa_gc",
        "release",
    ],
    "hazardous": [
        "hand_hygiene",
        "gowning",
        "gather",
        "calc",
        "measure",
        "mix",
        "fill",
        "label",
        "qa_visual",
        "release",
    ],
    "non_sterile": [
        "hand_hygiene",
        "gather",
        "calc",
        "measure",
        "mix",
        "fill",
        "label",
        "qa_visual",
        "release",
    ],
}


def _step_seed(kind: str) -> list[str]:
    return _DEFAULT_STEPS_BY_KIND.get(kind, _DEFAULT_STEPS_BY_KIND["non_sterile"])


@transaction.atomic
def create_order(
    *,
    tenant_id: UUID,
    formulation_id: UUID,
    prescription_id: Optional[UUID] = None,
    patient_profile_id: Optional[UUID] = None,
    requested_qty: int = 1,
    priority: str = "routine",
    assigned_compounder_id: Optional[UUID] = None,
    hood_id: str = "",
    **_: Any,
):
    from .models import CompoundingFormulation, CompoundingOrder, CompoundingStep

    formulation = CompoundingFormulation.objects.get(pk=formulation_id)
    order = CompoundingOrder.objects.create(
        tenant_id=tenant_id,
        prescription_id=prescription_id,
        patient_profile_id=patient_profile_id,
        formulation=formulation,
        requested_qty=requested_qty,
        priority=priority,
        assigned_compounder_id=assigned_compounder_id,
        hood_id=hood_id,
        status="requested",
    )
    seed = _step_seed(formulation.kind)
    for position, step_kind in enumerate(seed, start=1):
        CompoundingStep.objects.create(
            order=order,
            position=position,
            step_kind=step_kind,
            result="pending",
        )
    return order


@transaction.atomic
def verify_order(
    *,
    order_id: UUID,
    verifier_profile_id: Optional[UUID] = None,
    **_: Any,
):
    from .models import CompoundingOrder

    order = CompoundingOrder.objects.select_for_update().get(pk=order_id)
    if order.status not in {"requested", "ingredients_pulled"}:
        raise ValueError(f"Cannot verify order in status {order.status}")
    order.assigned_verifier_id = verifier_profile_id
    order.status = "verified"
    order.save(update_fields=["assigned_verifier_id", "status", "updated_at"])
    return order


@transaction.atomic
def record_step(
    *,
    order_id: UUID,
    step_id: Optional[UUID] = None,
    position: Optional[int] = None,
    performed_by: Optional[UUID] = None,
    result: str = "pass",
    notes: str = "",
    **_: Any,
):
    from .models import CompoundingOrder, CompoundingStep

    order = CompoundingOrder.objects.select_for_update().get(pk=order_id)
    if step_id is not None:
        step = CompoundingStep.objects.select_for_update().get(pk=step_id, order=order)
    elif position is not None:
        step = CompoundingStep.objects.select_for_update().get(order=order, position=position)
    else:
        raise ValueError("record_step requires step_id or position")
    step.performed_by = performed_by
    step.performed_at = timezone.now()
    step.result = result
    if notes:
        step.notes = notes
    step.save(update_fields=["performed_by", "performed_at", "result", "notes", "updated_at"])
    if order.status == "verified":
        order.status = "mixing"
        order.save(update_fields=["status", "updated_at"])
    return step


@transaction.atomic
def record_qa(
    *,
    order_id: UUID,
    kind: str,
    result: str = "pending",
    value: str = "",
    performed_by: Optional[UUID] = None,
    notes: str = "",
    **_: Any,
):
    from .models import CompoundingOrder, QATest

    order = CompoundingOrder.objects.select_for_update().get(pk=order_id)
    qa = QATest.objects.create(
        order=order,
        kind=kind,
        result=result,
        value=value,
        performed_by=performed_by,
        performed_at=timezone.now(),
        notes=notes,
    )
    if order.status in {"mixing", "verified"}:
        order.status = "qa_pending"
        order.save(update_fields=["status", "updated_at"])
    return qa


@transaction.atomic
def release(
    *,
    order_id: UUID,
    releaser_profile_id: UUID,
    lot_number: str,
    beyond_use_hours: Optional[int] = None,
    **_: Any,
):
    from .models import CompoundingOrder, QATest

    order = CompoundingOrder.objects.select_for_update().get(pk=order_id)
    if order.status == "released":
        return order
    if order.status in {"rejected", "expired"}:
        raise ValueError(f"Cannot release order in status {order.status}")

    qa_tests = list(QATest.objects.filter(order=order))
    if not qa_tests:
        raise ValueError("Cannot release: no QA tests recorded")
    if any(t.result != "pass" for t in qa_tests):
        raise ValueError("Cannot release: not all QA tests passed")

    hours = beyond_use_hours if beyond_use_hours is not None else order.formulation.beyond_use_hours
    now = timezone.now()
    order.lot_number = lot_number
    order.release_signed_by = releaser_profile_id
    order.released_at = now
    order.expires_at = now + timedelta(hours=int(hours))
    order.status = "released"
    order.save(
        update_fields=[
            "lot_number",
            "release_signed_by",
            "released_at",
            "expires_at",
            "status",
            "updated_at",
        ]
    )
    return order


@transaction.atomic
def reject(
    *,
    order_id: UUID,
    reject_reason: str,
    **_: Any,
):
    from .models import CompoundingOrder

    order = CompoundingOrder.objects.select_for_update().get(pk=order_id)
    if order.status == "released":
        raise ValueError("Cannot reject an already released order")
    order.status = "rejected"
    order.reject_reason = reject_reason
    order.save(update_fields=["status", "reject_reason", "updated_at"])
    return order
