"""Service layer for CyMed Imaging patient booking."""

from __future__ import annotations

import uuid
from datetime import date as date_type, time as time_type
from decimal import Decimal
from typing import Optional

from django.db import transaction
from django.utils import timezone

from .models import BookableStudy, ImagingBooking, ImagingSlot, ModalityRoom


DEFAULT_VAT_RATE = Decimal("0.15")


def _generate_booking_ref() -> str:
    return f"IMG-{uuid.uuid4().hex[:10].upper()}"


@transaction.atomic
def open_slot(
    *,
    tenant_id: uuid.UUID,
    room_id: uuid.UUID,
    date: date_type,
    start_time: time_type,
    end_time: time_type,
    capacity: int = 1,
) -> ImagingSlot:
    room = ModalityRoom.objects.select_for_update().get(pk=room_id, tenant_id=tenant_id)
    slot = ImagingSlot.objects.create(
        tenant_id=tenant_id,
        room=room,
        date=date,
        start_time=start_time,
        end_time=end_time,
        capacity=capacity,
        booked_count=0,
        status=ImagingSlot.Status.OPEN,
    )
    return slot


@transaction.atomic
def place_booking(
    *,
    tenant_id: uuid.UUID,
    patient_profile_id: uuid.UUID,
    study_id: uuid.UUID,
    slot_id: Optional[uuid.UUID] = None,
    referral_url: str = "",
    referring_provider_id: Optional[uuid.UUID] = None,
) -> ImagingBooking:
    study = BookableStudy.objects.get(pk=study_id, tenant_id=tenant_id)

    slot: Optional[ImagingSlot] = None
    if slot_id is not None:
        slot = ImagingSlot.objects.select_for_update().get(pk=slot_id, tenant_id=tenant_id)
        if slot.status not in (ImagingSlot.Status.OPEN,):
            raise ValueError("Slot is not open for booking")
        if slot.booked_count >= slot.capacity:
            raise ValueError("Slot has no remaining capacity")

    booking = ImagingBooking.objects.create(
        tenant_id=tenant_id,
        patient_profile_id=patient_profile_id,
        study=study,
        slot=slot,
        referral_url=referral_url,
        referring_provider_id=referring_provider_id,
        payment_status=ImagingBooking.PaymentStatus.UNPAID,
        status=ImagingBooking.Status.PLACED if slot else ImagingBooking.Status.DRAFT,
        booking_ref=_generate_booking_ref(),
    )

    if slot is not None:
        slot.booked_count = slot.booked_count + 1
        if slot.booked_count >= slot.capacity:
            slot.status = ImagingSlot.Status.FULL
        slot.save(update_fields=["booked_count", "status", "updated_at"] if hasattr(slot, "updated_at") else ["booked_count", "status"])

    try:
        from products.cymed.payments.models import UnifiedBill, BillLineItem

        currency = study.currency or "SAR"
        vat_rate = study.vat_rate if study.vat_rate is not None else DEFAULT_VAT_RATE
        subtotal = Decimal(study.price)
        vat_amount = (subtotal * Decimal(vat_rate)).quantize(Decimal("0.0001"))
        total = (subtotal + vat_amount).quantize(Decimal("0.0001"))

        bill = UnifiedBill.objects.create(
            tenant_id=tenant_id,
            patient_profile_id=patient_profile_id,
            currency=currency,
            subtotal=subtotal,
            vat_amount=vat_amount,
            total=total,
            status="unpaid",
            source_ref=booking.booking_ref,
        )
        BillLineItem.objects.create(
            tenant_id=tenant_id,
            bill=bill,
            description=study.name,
            quantity=Decimal("1.0000"),
            unit_price=subtotal,
            vat_rate=vat_rate,
            vat_amount=vat_amount,
            total=total,
        )
        booking.bill_id = bill.pk
        booking.save(update_fields=["bill_id"])
    except Exception:
        pass

    return booking


@transaction.atomic
def mark_paid(*, booking_id: uuid.UUID, payment_ref: str) -> ImagingBooking:
    booking = ImagingBooking.objects.select_for_update().get(pk=booking_id)
    booking.payment_status = ImagingBooking.PaymentStatus.PAID
    booking.payment_ref = payment_ref
    booking.status = ImagingBooking.Status.PAID
    booking.save(update_fields=["payment_status", "payment_ref", "status"])

    try:
        from products.cymed.imaging.orders.models import ImagingOrder

        order = ImagingOrder.objects.create(
            tenant_id=booking.tenant_id,
            patient_profile_id=booking.patient_profile_id,
            study_code=booking.study.code,
            source_ref=booking.booking_ref,
        )
        booking.order_id = order.pk
        booking.save(update_fields=["order_id"])
    except Exception:
        pass

    return booking


@transaction.atomic
def confirm_prep(
    *,
    booking_id: uuid.UUID,
    preparation_ok: bool,
    fasting_ok: bool,
) -> ImagingBooking:
    booking = ImagingBooking.objects.select_for_update().get(pk=booking_id)
    booking.preparation_confirmed = bool(preparation_ok)
    booking.fasting_confirmed = bool(fasting_ok)
    if preparation_ok and fasting_ok and booking.status == ImagingBooking.Status.PAID:
        booking.status = ImagingBooking.Status.SCHEDULED
    booking.save(update_fields=["preparation_confirmed", "fasting_confirmed", "status"])
    return booking


@transaction.atomic
def mark_arrived(booking_id: uuid.UUID) -> ImagingBooking:
    booking = ImagingBooking.objects.select_for_update().get(pk=booking_id)
    booking.status = ImagingBooking.Status.ARRIVED
    booking.save(update_fields=["status"])
    return booking


@transaction.atomic
def mark_completed(booking_id: uuid.UUID) -> ImagingBooking:
    booking = ImagingBooking.objects.select_for_update().get(pk=booking_id)
    booking.status = ImagingBooking.Status.COMPLETED
    booking.save(update_fields=["status"])
    return booking


@transaction.atomic
def cancel_booking(booking_id: uuid.UUID, reason: str = "") -> ImagingBooking:
    booking = ImagingBooking.objects.select_for_update().get(pk=booking_id)
    booking.status = ImagingBooking.Status.CANCELLED
    booking.save(update_fields=["status"])
    if booking.slot_id:
        slot = ImagingSlot.objects.select_for_update().get(pk=booking.slot_id)
        if slot.booked_count > 0:
            slot.booked_count = slot.booked_count - 1
        if slot.status == ImagingSlot.Status.FULL and slot.booked_count < slot.capacity:
            slot.status = ImagingSlot.Status.OPEN
        slot.save(update_fields=["booked_count", "status"])
    return booking
