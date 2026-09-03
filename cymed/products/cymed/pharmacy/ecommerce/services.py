"""CyMed Pharmacy E-commerce business services."""
from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any

from django.db import transaction
from django.utils import timezone

from .models import (
    Cart,
    CartItem,
    PharmacyOrder,
    PharmacyOrderItem,
    PharmacyProduct,
    RefillRequest,
)

VAT_RATE_DEFAULT = Decimal("0.15")
VAT_RATE_JOD = Decimal("0.16")


def _vat_rate_for_currency(currency: str) -> Decimal:
    if (currency or "").upper() == "JOD":
        return VAT_RATE_JOD
    return VAT_RATE_DEFAULT


@transaction.atomic
def add_to_cart(
    *,
    tenant_id: uuid.UUID,
    patient_profile_id: uuid.UUID,
    product_id: uuid.UUID,
    qty: int,
) -> CartItem:
    product = PharmacyProduct.objects.select_for_update().get(pk=product_id, tenant_id=tenant_id)
    cart, _created = Cart.objects.get_or_create(
        tenant_id=tenant_id,
        patient_profile_id=patient_profile_id,
        status=Cart.Status.OPEN,
    )
    item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={
            "qty": qty,
            "unit_price": product.price,
            "snapshot_name": product.name,
        },
    )
    if not created:
        item.qty = item.qty + qty
        item.unit_price = product.price
        item.snapshot_name = product.name
        item.save(update_fields=["qty", "unit_price", "snapshot_name", "updated_at"])
    return item


@transaction.atomic
def checkout_cart(
    *,
    cart_id: uuid.UUID,
    fulfillment: str,
    delivery_address: dict | None = None,
    delivery_slot: tuple | None = None,
) -> PharmacyOrder:
    cart = Cart.objects.select_for_update().get(pk=cart_id, status=Cart.Status.OPEN)
    items = list(CartItem.objects.select_related("product").filter(cart=cart))
    if not items:
        raise ValueError("Cart is empty")

    currency = items[0].product.currency
    vat_rate = _vat_rate_for_currency(currency)

    subtotal = Decimal("0")
    for it in items:
        subtotal += (it.unit_price or Decimal("0")) * Decimal(it.qty)
    vat_amount = (subtotal * vat_rate).quantize(Decimal("0.0001"))
    total = (subtotal + vat_amount).quantize(Decimal("0.0001"))

    slot_start = None
    slot_end = None
    if delivery_slot and len(delivery_slot) == 2:
        slot_start, slot_end = delivery_slot

    order = PharmacyOrder.objects.create(
        tenant_id=cart.tenant_id,
        patient_profile_id=cart.patient_profile_id,
        source=PharmacyOrder.Source.WEB,
        status=PharmacyOrder.Status.PLACED,
        fulfillment=fulfillment,
        subtotal=subtotal,
        vat=vat_amount,
        discount=Decimal("0"),
        total=total,
        currency=currency,
        delivery_address=delivery_address or {},
        delivery_slot_start=slot_start,
        delivery_slot_end=slot_end,
    )

    for it in items:
        line_total = (it.unit_price or Decimal("0")) * Decimal(it.qty)
        PharmacyOrderItem.objects.create(
            order=order,
            product_id=it.product_id,
            product_name=it.snapshot_name or it.product.name,
            qty=it.qty,
            unit_price=it.unit_price,
            line_total=line_total,
            is_prescription=bool(it.product.requires_prescription),
        )

    try:
        from products.cymed.payments.models import BillLineItem, UnifiedBill

        bill = UnifiedBill.objects.create(
            tenant_id=cart.tenant_id,
            patient_profile_id=cart.patient_profile_id,
            currency=currency,
            subtotal=subtotal,
            vat=vat_amount,
            total=total,
            source="pharmacy_order",
            source_ref=str(order.pk),
        )
        for it in items:
            BillLineItem.objects.create(
                bill=bill,
                description=it.snapshot_name or it.product.name,
                qty=it.qty,
                unit_price=it.unit_price,
                line_total=(it.unit_price or Decimal("0")) * Decimal(it.qty),
            )
        order.bill_id = bill.pk
        order.save(update_fields=["bill_id", "updated_at"])
    except Exception:
        pass

    cart.status = Cart.Status.CHECKED_OUT
    cart.save(update_fields=["status", "updated_at"])

    return order


@transaction.atomic
def submit_refill_request(
    *,
    tenant_id: uuid.UUID,
    patient_profile_id: uuid.UUID,
    drug_name: str,
    qty: int,
    drug_id: uuid.UUID | None = None,
    original_prescription_id: uuid.UUID | None = None,
    delivery_address: dict | None = None,
) -> RefillRequest:
    return RefillRequest.objects.create(
        tenant_id=tenant_id,
        patient_profile_id=patient_profile_id,
        drug_id=drug_id,
        drug_name=drug_name,
        qty=qty,
        original_prescription_id=original_prescription_id,
        delivery_address=delivery_address or {},
        status=RefillRequest.Status.SUBMITTED,
    )


@transaction.atomic
def verify_refill(
    *,
    refill_id: uuid.UUID,
    approved: bool,
    pharmacist_notes: str = "",
) -> RefillRequest:
    refill = RefillRequest.objects.select_for_update().get(pk=refill_id)
    refill.status = RefillRequest.Status.VERIFIED if approved else RefillRequest.Status.REJECTED
    if pharmacist_notes:
        refill.pharmacist_notes = pharmacist_notes
    refill.save(update_fields=["status", "pharmacist_notes", "updated_at"])
    return refill


@transaction.atomic
def mark_ready(order_id: uuid.UUID) -> PharmacyOrder:
    order = PharmacyOrder.objects.select_for_update().get(pk=order_id)
    order.status = PharmacyOrder.Status.READY
    order.save(update_fields=["status", "updated_at"])
    return order


@transaction.atomic
def mark_shipped(order_id: uuid.UUID, delivery_id: uuid.UUID | None = None) -> PharmacyOrder:
    order = PharmacyOrder.objects.select_for_update().get(pk=order_id)
    order.status = PharmacyOrder.Status.SHIPPED
    if delivery_id is not None:
        order.delivery_id = delivery_id
    order.save(update_fields=["status", "delivery_id", "updated_at"])
    return order


@transaction.atomic
def mark_delivered(order_id: uuid.UUID) -> PharmacyOrder:
    order = PharmacyOrder.objects.select_for_update().get(pk=order_id)
    order.status = PharmacyOrder.Status.DELIVERED
    order.save(update_fields=["status", "updated_at"])
    return order
