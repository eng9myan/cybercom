from django.db import models

from platform.common.models import BaseModel


class Event(BaseModel):
    """A ticketed event with capacity and attendee registration — distinct
    from scheduler.Event, which is a plain calendar entry with no
    ticketing/registration concept at all."""

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    venue = models.CharField(max_length=255, blank=True)
    start_at = models.DateTimeField()
    end_at = models.DateTimeField()
    capacity = models.PositiveIntegerField(default=0, help_text="0 = unlimited.")
    is_published = models.BooleanField(default=False)

    class Meta:
        db_table = "cycom_events_events"
        ordering = ["-start_at"]

    def __str__(self):
        return self.name

    @property
    def registered_count(self):
        return self.registrations.exclude(status="cancelled").count()

    @property
    def is_sold_out(self):
        return self.capacity > 0 and self.registered_count >= self.capacity


class TicketType(BaseModel):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="ticket_types")
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    quantity_available = models.PositiveIntegerField(default=0, help_text="0 = unlimited.")

    class Meta:
        db_table = "cycom_events_ticket_types"
        ordering = ["price"]

    def __str__(self):
        return f"{self.name} ({self.event})"

    @property
    def registered_count(self):
        return self.registrations.exclude(status="cancelled").count()

    @property
    def is_sold_out(self):
        return self.quantity_available > 0 and self.registered_count >= self.quantity_available


class Registration(BaseModel):
    STATUS_CHOICES = [
        ("registered", "Registered"),
        ("checked_in", "Checked In"),
        ("cancelled", "Cancelled"),
    ]

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="registrations")
    ticket_type = models.ForeignKey(
        TicketType, on_delete=models.SET_NULL, null=True, blank=True, related_name="registrations"
    )
    attendee_name = models.CharField(max_length=255)
    attendee_email = models.EmailField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="registered")
    checked_in_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "cycom_events_registrations"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.attendee_name} — {self.event} ({self.status})"
