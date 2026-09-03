"""Service functions for phlebotomist home-collection workflows."""

from __future__ import annotations

from datetime import date as _date, time as _time
from typing import Any, Optional

from django.db import transaction
from django.utils import timezone

from .models import (
    HomeCollectionBooking,
    HomeCollectionEvent,
    HomeCollectionSlot,
    Phlebotomist,
)


@transaction.atomic
def open_slot(
    *,
    tenant_id,
    phlebotomist_id,
    date: _date,
    start_time: _time,
    end_time: _time,
    capacity: int = 1,
) -> HomeCollectionSlot:
    phlebotomist = Phlebotomist.objects.get(pk=phlebotomist_id)
    slot = HomeCollectionSlot.objects.create(
        tenant_id=tenant_id,
        phlebotomist=phlebotomist,
        date=date,
        start_time=start_time,
        end_time=end_time,
        capacity=capacity,
        booked_count=0,
        status=HomeCollectionSlot.Status.OPEN,
    )
    return slot


@transaction.atomic
def book_home_collection(
    *,
    tenant_id,
    patient_profile_id,
    slot_id,
    address: dict,
    lat=None,
    lng=None,
    tests_requested: list,
    fasting_required: bool = False,
    special_instructions: str = "",
    order_id=None,
) -> HomeCollectionBooking:
    slot = HomeCollectionSlot.objects.select_for_update().get(pk=slot_id)
    if slot.status in (
        HomeCollectionSlot.Status.FULL,
        HomeCollectionSlot.Status.BLOCKED,
        HomeCollectionSlot.Status.CANCELLED,
    ):
        raise ValueError(f"Slot {slot_id} is not open for booking")
    if slot.booked_count >= slot.capacity:
        raise ValueError(f"Slot {slot_id} is at capacity")

    booking = HomeCollectionBooking.objects.create(
        tenant_id=tenant_id,
        patient_profile_id=patient_profile_id,
        order_id=order_id,
        slot=slot,
        phlebotomist=slot.phlebotomist,
        address=address or {},
        lat=lat,
        lng=lng,
        tests_requested=tests_requested or [],
        fasting_required=fasting_required,
        special_instructions=special_instructions,
        status=HomeCollectionBooking.Status.REQUESTED,
        payment_status=HomeCollectionBooking.PaymentStatus.UNPAID,
    )

    slot.booked_count += 1
    if slot.booked_count >= slot.capacity:
        slot.status = HomeCollectionSlot.Status.FULL
    slot.save(update_fields=["booked_count", "status", "updated_at"])

    HomeCollectionEvent.objects.create(
        booking=booking,
        kind=HomeCollectionEvent.Kind.CREATED,
        lat=lat,
        lng=lng,
        note="Booking created",
    )
    return booking


@transaction.atomic
def assign_phlebotomist(*, booking_id, phlebotomist_id) -> HomeCollectionBooking:
    booking = HomeCollectionBooking.objects.select_for_update().get(pk=booking_id)
    phlebotomist = Phlebotomist.objects.get(pk=phlebotomist_id)
    booking.phlebotomist = phlebotomist
    if booking.status == HomeCollectionBooking.Status.REQUESTED:
        booking.status = HomeCollectionBooking.Status.CONFIRMED
    booking.save(update_fields=["phlebotomist", "status", "updated_at"])
    HomeCollectionEvent.objects.create(
        booking=booking,
        kind=HomeCollectionEvent.Kind.ASSIGNED,
        note=f"Assigned phlebotomist {phlebotomist_id}",
    )
    return booking


@transaction.atomic
def update_status(
    *,
    booking_id,
    status: str,
    lat=None,
    lng=None,
    note: str = "",
) -> HomeCollectionBooking:
    booking = HomeCollectionBooking.objects.select_for_update().get(pk=booking_id)
    booking.status = status
    now = timezone.now()
    update_fields = ["status", "updated_at"]

    if status == HomeCollectionBooking.Status.COLLECTED and not booking.collection_started_at:
        booking.collection_started_at = now
        update_fields.append("collection_started_at")

    booking.save(update_fields=update_fields)

    kind_map = {
        HomeCollectionBooking.Status.DISPATCHED: HomeCollectionEvent.Kind.DISPATCHED,
        HomeCollectionBooking.Status.EN_ROUTE: HomeCollectionEvent.Kind.DISPATCHED,
        HomeCollectionBooking.Status.ARRIVED: HomeCollectionEvent.Kind.ARRIVED,
        HomeCollectionBooking.Status.COLLECTED: HomeCollectionEvent.Kind.COLLECTED,
        HomeCollectionBooking.Status.DELIVERED_TO_LAB: HomeCollectionEvent.Kind.DELIVERED,
        HomeCollectionBooking.Status.CANCELLED: HomeCollectionEvent.Kind.CANCELLED,
        HomeCollectionBooking.Status.NO_SHOW: HomeCollectionEvent.Kind.CUSTOMER_ABSENT,
    }
    event_kind = kind_map.get(status, HomeCollectionEvent.Kind.DISPATCHED)

    HomeCollectionEvent.objects.create(
        booking=booking,
        kind=event_kind,
        lat=lat,
        lng=lng,
        note=note,
    )
    return booking


@transaction.atomic
def complete_collection(
    *,
    booking_id,
    specimen_barcodes: list[str],
    proof: dict,
) -> HomeCollectionBooking:
    booking = HomeCollectionBooking.objects.select_for_update().get(pk=booking_id)
    now = timezone.now()
    booking.specimen_barcodes = list(specimen_barcodes or [])
    booking.proof_of_collection = dict(proof or {})
    booking.status = HomeCollectionBooking.Status.COLLECTED
    if not booking.collection_started_at:
        booking.collection_started_at = now
    booking.collection_completed_at = now
    booking.save(update_fields=[
        "specimen_barcodes",
        "proof_of_collection",
        "status",
        "collection_started_at",
        "collection_completed_at",
        "updated_at",
    ])
    HomeCollectionEvent.objects.create(
        booking=booking,
        kind=HomeCollectionEvent.Kind.COLLECTED,
        note=f"Collected {len(booking.specimen_barcodes)} specimens",
    )
    return booking


@transaction.atomic
def cancel_booking(
    *,
    booking_id,
    reason: str,
    by_patient: bool = False,
) -> HomeCollectionBooking:
    booking = HomeCollectionBooking.objects.select_for_update().get(pk=booking_id)
    booking.status = HomeCollectionBooking.Status.CANCELLED
    booking.save(update_fields=["status", "updated_at"])

    slot = HomeCollectionSlot.objects.select_for_update().get(pk=booking.slot_id)
    if slot.booked_count > 0:
        slot.booked_count -= 1
    if slot.status == HomeCollectionSlot.Status.FULL and slot.booked_count < slot.capacity:
        slot.status = HomeCollectionSlot.Status.OPEN
    slot.save(update_fields=["booked_count", "status", "updated_at"])

    prefix = "patient" if by_patient else "operator"
    HomeCollectionEvent.objects.create(
        booking=booking,
        kind=HomeCollectionEvent.Kind.CANCELLED,
        note=f"Cancelled by {prefix}: {reason}",
    )
    return booking
