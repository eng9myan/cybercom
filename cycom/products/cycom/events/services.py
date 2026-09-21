from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from products.cycom.events.models import Event, Registration, TicketType


@transaction.atomic
def register_attendee(
    event: Event, *, attendee_name: str, attendee_email: str = "", ticket_type: TicketType | None = None
) -> Registration:
    if event.is_sold_out:
        raise ValidationError(f"Event '{event.name}' is sold out (capacity {event.capacity}).")
    if ticket_type is not None:
        if ticket_type.event_id != event.id:
            raise ValidationError("ticket_type does not belong to this event.")
        if ticket_type.is_sold_out:
            raise ValidationError(f"Ticket type '{ticket_type.name}' is sold out.")

    return Registration.objects.create(
        tenant_id=event.tenant_id,
        event=event,
        ticket_type=ticket_type,
        attendee_name=attendee_name,
        attendee_email=attendee_email,
    )


def check_in(registration: Registration) -> Registration:
    if registration.status != "registered":
        raise ValidationError(f"Registration is '{registration.status}', must be 'registered' to check in.")
    registration.status = "checked_in"
    registration.checked_in_at = timezone.now()
    registration.save(update_fields=["status", "checked_in_at", "updated_at"])
    return registration


def cancel_registration(registration: Registration) -> Registration:
    if registration.status != "registered":
        raise ValidationError(f"Registration is '{registration.status}', cannot cancel.")
    registration.status = "cancelled"
    registration.save(update_fields=["status", "updated_at"])
    return registration
