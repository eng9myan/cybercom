"""Service functions for the DTC test catalog workflows."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from django.db import transaction
from django.utils import timezone

from .models import DtcKit, DtcOrder, DtcProduct


def _mint_unified_bill(*, tenant_id, patient_profile_id, product: DtcProduct) -> Any:
    try:
        from products.cymed.billing.models import UnifiedBill
    except Exception:
        return None
    gross = Decimal(product.price) * (Decimal("1") + Decimal(product.vat_rate))
    try:
        bill = UnifiedBill.objects.create(
            tenant_id=tenant_id,
            patient_profile_id=patient_profile_id,
            currency=product.currency,
            total_amount=gross,
            status="pending",
            source="dtc_catalog",
            metadata={"product_code": product.code, "product_id": str(product.id)},
        )
        return bill
    except Exception:
        return None


@transaction.atomic
def place_dtc_order(
    *,
    tenant_id,
    patient_profile_id,
    product_id,
    shipping_address: dict,
) -> DtcOrder:
    product = DtcProduct.objects.select_for_update().get(pk=product_id)
    if not product.active:
        raise ValueError("Product is not active")
    if product.stock_qty > -1:
        if product.stock_qty <= 0:
            raise ValueError("Product is out of stock")
        product.stock_qty = product.stock_qty - 1
        product.save(update_fields=["stock_qty", "updated_at"] if hasattr(product, "updated_at") else ["stock_qty"])
    bill = _mint_unified_bill(
        tenant_id=tenant_id,
        patient_profile_id=patient_profile_id,
        product=product,
    )
    order = DtcOrder.objects.create(
        tenant_id=tenant_id,
        patient_profile_id=patient_profile_id,
        product=product,
        shipping_address=shipping_address or {},
        status=DtcOrder.Status.PLACED,
        bill_id=getattr(bill, "id", None) if bill is not None else None,
    )
    return order


@transaction.atomic
def dispatch_kit(*, order_id, kit_barcode: str) -> DtcOrder:
    order = DtcOrder.objects.select_for_update().get(pk=order_id)
    kit = DtcKit.objects.select_for_update().get(kit_barcode=kit_barcode)
    if kit.product_id != order.product_id:
        raise ValueError("Kit product mismatch")
    if kit.status not in {DtcKit.Status.IN_STOCK}:
        raise ValueError("Kit is not available for dispatch")
    kit.status = DtcKit.Status.DISPATCHED
    kit.save(update_fields=["status"])
    order.kit = kit
    order.status = DtcOrder.Status.KIT_DISPATCHED
    order.save(update_fields=["kit", "status"])
    return order


@transaction.atomic
def activate_kit(*, kit_barcode: str) -> DtcOrder:
    kit = DtcKit.objects.select_for_update().get(kit_barcode=kit_barcode)
    order = DtcOrder.objects.select_for_update().filter(kit=kit).order_by("-created_at").first()
    if order is None:
        raise ValueError("No order found for this kit")
    kit.status = DtcKit.Status.ACTIVATED
    kit.save(update_fields=["status"])
    order.status = DtcOrder.Status.KIT_ACTIVATED
    order.save(update_fields=["status"])
    return order


@transaction.atomic
def sample_received(*, order_id) -> DtcOrder:
    order = DtcOrder.objects.select_for_update().get(pk=order_id)
    order.status = DtcOrder.Status.SAMPLE_RECEIVED
    order.save(update_fields=["status"])
    return order


@transaction.atomic
def mark_results_ready(*, order_id) -> DtcOrder:
    order = DtcOrder.objects.select_for_update().get(pk=order_id)
    order.status = DtcOrder.Status.RESULTS_READY
    order.save(update_fields=["status"])
    return order


@transaction.atomic
def schedule_consultation(*, order_id, at: datetime) -> DtcOrder:
    order = DtcOrder.objects.select_for_update().get(pk=order_id)
    if at is None:
        raise ValueError("Consultation datetime is required")
    order.consultation_scheduled_at = at
    order.save(update_fields=["consultation_scheduled_at"])
    return order


@transaction.atomic
def cancel_order(*, order_id, reason: str) -> DtcOrder:
    order = DtcOrder.objects.select_for_update().get(pk=order_id)
    if order.status in {DtcOrder.Status.DELIVERED_TO_PATIENT, DtcOrder.Status.REFUNDED}:
        raise ValueError("Order cannot be cancelled in its current state")
    order.status = DtcOrder.Status.CANCELLED
    note = f"[cancelled {timezone.now().isoformat()}] {reason}".strip()
    order.consultation_notes = (order.consultation_notes + "\n" + note).strip() if order.consultation_notes else note
    order.save(update_fields=["status", "consultation_notes"])
    if order.kit_id and order.kit and order.kit.status in {DtcKit.Status.DISPATCHED, DtcKit.Status.ACTIVATED}:
        order.kit.status = DtcKit.Status.RETURNED_FULL
        order.kit.save(update_fields=["status"])
    if order.product_id and order.product and order.product.stock_qty > -1:
        order.product.stock_qty = order.product.stock_qty + 1
        order.product.save(update_fields=["stock_qty"])
    return order
