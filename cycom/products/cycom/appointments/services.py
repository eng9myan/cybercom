from datetime import timedelta

from django.db import transaction
from rest_framework.exceptions import ValidationError

from products.cycom.appointments.models import AppointmentType, Booking, Resource


def _is_within_availability(resource: Resource, start_at, end_at) -> bool:
    if start_at.date() != end_at.date():
        return False  # no overnight-spanning bookings
    weekday = start_at.weekday()
    return resource.availability_slots.filter(
        weekday=weekday, start_time__lte=start_at.time(), end_time__gte=end_at.time()
    ).exists()


def _overlaps_existing_booking(resource: Resource, start_at, end_at, buffer_minutes, exclude_id=None) -> bool:
    occupied_end = end_at + timedelta(minutes=buffer_minutes)
    existing = Booking.objects.filter(resource=resource, status="confirmed")
    if exclude_id:
        existing = existing.exclude(id=exclude_id)
    for booking in existing.select_related("appointment_type"):
        existing_occupied_end = booking.end_at + timedelta(minutes=booking.appointment_type.buffer_minutes)
        if start_at < existing_occupied_end and booking.start_at < occupied_end:
            return True
    return False


@transaction.atomic
def book_appointment(
    *, resource: Resource, appointment_type: AppointmentType, start_at, customer_name: str,
    customer_email: str = "",
) -> Booking:
    if not appointment_type.is_active:
        raise ValidationError(f"Appointment type '{appointment_type.name}' is not active.")
    if not resource.is_active:
        raise ValidationError(f"Resource '{resource.name}' is not active.")

    end_at = start_at + timedelta(minutes=appointment_type.duration_minutes)

    if not _is_within_availability(resource, start_at, end_at):
        raise ValidationError(f"{resource.name} is not available at {start_at}.")
    if _overlaps_existing_booking(resource, start_at, end_at, appointment_type.buffer_minutes):
        raise ValidationError(f"{resource.name} is already booked at that time.")

    return Booking.objects.create(
        tenant_id=resource.tenant_id,
        appointment_type=appointment_type,
        resource=resource,
        customer_name=customer_name,
        customer_email=customer_email,
        start_at=start_at,
        end_at=end_at,
    )


def cancel_booking(booking: Booking) -> Booking:
    if booking.status != "confirmed":
        raise ValidationError(f"Booking is '{booking.status}', cannot cancel.")
    booking.status = "cancelled"
    booking.save(update_fields=["status", "updated_at"])
    return booking


def complete_booking(booking: Booking) -> Booking:
    if booking.status != "confirmed":
        raise ValidationError(f"Booking is '{booking.status}', cannot complete.")
    booking.status = "completed"
    booking.save(update_fields=["status", "updated_at"])
    return booking
