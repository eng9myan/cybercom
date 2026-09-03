"""Cart → order → bill orchestration."""
from __future__ import annotations

from decimal import Decimal

from django.utils import timezone

from .models import ClinicOrder, ClinicOrderItem, ClinicProduct

VAT_RATE = Decimal("0.15")   # KSA 15%; overridden per country in production


def add_to_cart(*, tenant_id, patient_profile_id, product_id, qty: int = 1) -> ClinicOrder:
    product = ClinicProduct.objects.get(id=product_id, tenant_id=tenant_id, active=True)
    order, _ = ClinicOrder.objects.get_or_create(
        tenant_id=tenant_id, patient_profile_id=patient_profile_id,
        status="cart",
    )
    item = order.items.filter(product=product).first()
    if item:
        item.qty += qty
        item.amount = item.qty * item.unit_price
        item.save(update_fields=["qty", "amount", "updated_at"])
    else:
        ClinicOrderItem.objects.create(
            order=order, product=product,
            qty=qty, unit_price=product.price, amount=product.price * qty,
        )
    _recompute(order)
    return order


def place_order(*, order_id, delivery_address: str = "") -> ClinicOrder:
    order = ClinicOrder.objects.get(id=order_id, status="cart")
    order.status = "placed"
    order.delivery_address = delivery_address
    order.placed_at = timezone.now()
    order.save(update_fields=["status", "delivery_address", "placed_at", "updated_at"])
    _mint_bill(order)
    return order


def cancel_order(*, order_id) -> ClinicOrder:
    order = ClinicOrder.objects.get(id=order_id)
    order.status = "cancelled"
    order.save(update_fields=["status", "updated_at"])
    return order


def mark_shipped(*, order_id) -> ClinicOrder:
    order = ClinicOrder.objects.get(id=order_id)
    order.status = "shipped"
    order.shipped_at = timezone.now()
    order.save(update_fields=["status", "shipped_at", "updated_at"])
    return order


def mark_delivered(*, order_id) -> ClinicOrder:
    order = ClinicOrder.objects.get(id=order_id)
    order.status = "delivered"
    order.delivered_at = timezone.now()
    order.save(update_fields=["status", "delivered_at", "updated_at"])
    return order


def _recompute(order: ClinicOrder):
    subtotal = sum((i.amount for i in order.items.all()), Decimal("0"))
    order.subtotal = subtotal
    order.vat = (subtotal * VAT_RATE).quantize(Decimal("0.01"))
    order.total = order.subtotal + order.vat
    order.save(update_fields=["subtotal", "vat", "total", "updated_at"])


def _mint_bill(order: ClinicOrder):
    """Create a UnifiedBill for this order so patient can pay via existing flow."""
    try:
        from products.cymed.payments.models import BillLineItem, UnifiedBill
    except ImportError:
        return
    bill = UnifiedBill.objects.create(
        patient_profile_id=order.patient_profile_id,
        subtotal=order.subtotal, vat=order.vat, total=order.total,
        patient_due=order.total,
        status="patient_due",
    )
    for i in order.items.all():
        BillLineItem.objects.create(
            bill=bill,
            provider_tenant_id=order.tenant_id,
            service_code=i.product.sku,
            service_name=i.product.name_en,
            quantity=i.qty,
            unit_price=i.unit_price,
            amount=i.amount,
            category="supply" if i.product.kind in ("supplement", "skincare") else "other",
        )
    order.bill_id = bill.id
    order.save(update_fields=["bill_id", "updated_at"])
