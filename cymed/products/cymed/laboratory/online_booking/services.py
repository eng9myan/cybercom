"""Service layer for CyMed Laboratory Online Test Booking."""
from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any

from django.db import transaction
from django.utils import timezone

from .models import BookableTest, LabAppointmentSlot, LabBooking, LabPackage

DEFAULT_VAT_RATE = Decimal("0.15")
QUANT = Decimal("0.0001")


def _q(value: Decimal) -> Decimal:
    return value.quantize(QUANT)


def _collect_lines(
    *,
    tenant_id: Any,
    test_ids: list,
    package_ids: list,
) -> tuple[list[dict], Decimal, Decimal, Decimal, Decimal, str]:
    lines: list[dict] = []
    subtotal = Decimal("0")
    discount_total = Decimal("0")
    vat_total = Decimal("0")
    currency = "SAR"
    vat_rate = DEFAULT_VAT_RATE

    tests_qs = BookableTest.objects.filter(tenant_id=tenant_id, id__in=test_ids or [])
    for test in tests_qs:
        price = Decimal(test.price)
        line_vat = price * Decimal(test.vat_rate)
        subtotal += price
        vat_total += line_vat
        currency = test.currency
        vat_rate = Decimal(test.vat_rate)
        lines.append({
            "kind": "test",
            "id": str(test.id),
            "code": test.code,
            "name": test.name,
            "price": str(_q(price)),
            "vat_rate": str(test.vat_rate),
            "vat": str(_q(line_vat)),
            "currency": test.currency,
        })

    packages_qs = LabPackage.objects.filter(tenant_id=tenant_id, id__in=package_ids or [])
    for package in packages_qs:
        price = Decimal(package.price)
        pkg_discount = price * (Decimal(package.discount_percent) / Decimal("100"))
        net_price = price - pkg_discount
        line_vat = net_price * Decimal(package.vat_rate)
        subtotal += price
        discount_total += pkg_discount
        vat_total += line_vat
        currency = package.currency
        vat_rate = Decimal(package.vat_rate)
        lines.append({
            "kind": "package",
            "id": str(package.id),
            "code": package.code,
            "name": package.name,
            "price": str(_q(price)),
            "discount": str(_q(pkg_discount)),
            "vat_rate": str(package.vat_rate),
            "vat": str(_q(line_vat)),
            "currency": package.currency,
        })

    total = subtotal - discount_total + vat_total
    return lines, _q(subtotal), _q(discount_total), _q(vat_total), _q(total), currency


def open_slot(
    *,
    tenant_id: Any,
    facility_id: Any = None,
    date: Any,
    start_time: Any,
    end_time: Any,
    capacity: int = 1,
    collection_mode: str = "in_lab",
) -> LabAppointmentSlot:
    slot = LabAppointmentSlot.objects.create(
        tenant_id=tenant_id,
        facility_id=facility_id,
        date=date,
        start_time=start_time,
        end_time=end_time,
        capacity=int(capacity),
        booked_count=0,
        collection_mode=collection_mode,
        status=LabAppointmentSlot.Status.OPEN,
    )
    return slot


def build_cart(
    *,
    tenant_id: Any,
    patient_profile_id: Any,
    test_ids: list,
    package_ids: list,
) -> dict:
    lines, subtotal, discount, vat, total, currency = _collect_lines(
        tenant_id=tenant_id,
        test_ids=test_ids,
        package_ids=package_ids,
    )
    return {
        "tenant_id": str(tenant_id) if tenant_id else None,
        "patient_profile_id": str(patient_profile_id) if patient_profile_id else None,
        "lines": lines,
        "subtotal": str(subtotal),
        "discount": str(discount),
        "vat": str(vat),
        "total": str(total),
        "currency": currency,
    }


@transaction.atomic
def place_booking(
    *,
    tenant_id: Any,
    patient_profile_id: Any,
    test_ids: list,
    package_ids: list,
    slot_id: Any = None,
    collection_mode: str = "in_lab",
) -> LabBooking:
    lines, subtotal, discount, vat, total, currency = _collect_lines(
        tenant_id=tenant_id,
        test_ids=test_ids,
        package_ids=package_ids,
    )

    slot = None
    if slot_id:
        slot = LabAppointmentSlot.objects.select_for_update().get(pk=slot_id)
        slot.booked_count = int(slot.booked_count) + 1
        if slot.booked_count >= slot.capacity:
            slot.status = LabAppointmentSlot.Status.FULL
        slot.save(update_fields=["booked_count", "status", "updated_at"] if _has_updated_at(slot) else ["booked_count", "status"])

    booking_ref = f"LB-{uuid.uuid4().hex[:10].upper()}"

    booking = LabBooking.objects.create(
        tenant_id=tenant_id,
        patient_profile_id=patient_profile_id,
        slot=slot,
        tests=[l for l in lines if l.get("kind") == "test"],
        packages=[l for l in lines if l.get("kind") == "package"],
        subtotal=subtotal,
        discount=discount,
        vat=vat,
        total=total,
        currency=currency,
        payment_status=LabBooking.PaymentStatus.UNPAID,
        status=LabBooking.Status.PLACED,
        booking_ref=booking_ref,
    )

    try:
        from products.cymed.payments.models import BillLineItem, UnifiedBill

        bill = UnifiedBill.objects.create(
            tenant_id=tenant_id,
            patient_profile_id=patient_profile_id,
            subtotal=subtotal,
            discount=discount,
            vat=vat,
            total=total,
            currency=currency,
            status="unpaid",
            source_module="cymed_lab_online_booking",
            source_ref=str(booking.id),
        )
        for line in lines:
            BillLineItem.objects.create(
                bill=bill,
                description=f"{line.get('kind','item').title()}: {line.get('name','')}",
                quantity=Decimal("1"),
                unit_price=Decimal(line.get("price", "0")),
                vat_rate=Decimal(line.get("vat_rate", str(DEFAULT_VAT_RATE))),
                total=Decimal(line.get("price", "0")) + Decimal(line.get("vat", "0")),
            )
        booking.bill_id = bill.id
        booking.save(update_fields=["bill_id"])
    except Exception:
        pass

    return booking


def _has_updated_at(instance: Any) -> bool:
    try:
        return any(f.name == "updated_at" for f in instance._meta.fields)
    except Exception:
        return False


@transaction.atomic
def mark_paid(*, booking_id: Any, payment_ref: str) -> LabBooking:
    booking = LabBooking.objects.select_for_update().get(pk=booking_id)
    booking.payment_status = LabBooking.PaymentStatus.PAID
    booking.payment_ref = payment_ref or ""
    booking.status = LabBooking.Status.PAID
    booking.save(update_fields=["payment_status", "payment_ref", "status"])
    return booking


@transaction.atomic
def schedule_collection(
    *,
    booking_id: Any,
    home_collection_booking_id: Any = None,
    slot_id: Any = None,
) -> LabBooking:
    booking = LabBooking.objects.select_for_update().get(pk=booking_id)
    if home_collection_booking_id:
        booking.home_collection_booking_id = home_collection_booking_id
    if slot_id:
        slot = LabAppointmentSlot.objects.select_for_update().get(pk=slot_id)
        if booking.slot_id != slot.id:
            slot.booked_count = int(slot.booked_count) + 1
            if slot.booked_count >= slot.capacity:
                slot.status = LabAppointmentSlot.Status.FULL
            slot.save(update_fields=["booked_count", "status"])
            booking.slot = slot
    booking.status = LabBooking.Status.SCHEDULED
    booking.save(update_fields=["home_collection_booking_id", "slot", "status"])
    return booking


@transaction.atomic
def cancel_booking(*, booking_id: Any, reason: str) -> LabBooking:
    booking = LabBooking.objects.select_for_update().get(pk=booking_id)
    if booking.slot_id:
        slot = LabAppointmentSlot.objects.select_for_update().get(pk=booking.slot_id)
        slot.booked_count = max(0, int(slot.booked_count) - 1)
        if slot.status == LabAppointmentSlot.Status.FULL and slot.booked_count < slot.capacity:
            slot.status = LabAppointmentSlot.Status.OPEN
        slot.save(update_fields=["booked_count", "status"])
    booking.status = LabBooking.Status.CANCELLED
    booking.save(update_fields=["status"])
    return booking
