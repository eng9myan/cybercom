from django.db import models

from platform.common.models import BaseModel

WEEKDAY_CHOICES = [
    (0, "Monday"), (1, "Tuesday"), (2, "Wednesday"), (3, "Thursday"),
    (4, "Friday"), (5, "Saturday"), (6, "Sunday"),
]


class AppointmentType(BaseModel):
    """A bookable service — its duration drives every booking's end_at, and
    buffer_minutes is the mandatory gap enforced after each booking before
    the same resource can be booked again."""

    name = models.CharField(max_length=255)
    duration_minutes = models.PositiveIntegerField()
    buffer_minutes = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "cycom_appointments_types"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Resource(BaseModel):
    """A bookable staff member, room, or piece of equipment."""

    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "cycom_appointments_resources"
        ordering = ["name"]

    def __str__(self):
        return self.name


class AvailabilitySlot(BaseModel):
    """A resource's recurring weekly working window. A booking must fall
    entirely inside one of these on the same weekday — no overnight-spanning
    windows."""

    resource = models.ForeignKey(Resource, on_delete=models.CASCADE, related_name="availability_slots")
    weekday = models.PositiveSmallIntegerField(choices=WEEKDAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        db_table = "cycom_appointments_availability_slots"
        ordering = ["weekday", "start_time"]

    def __str__(self):
        return f"{self.resource} — {self.get_weekday_display()} {self.start_time}-{self.end_time}"


class Booking(BaseModel):
    STATUS_CHOICES = [
        ("confirmed", "Confirmed"),
        ("cancelled", "Cancelled"),
        ("completed", "Completed"),
    ]

    appointment_type = models.ForeignKey(
        AppointmentType, on_delete=models.PROTECT, related_name="bookings"
    )
    resource = models.ForeignKey(Resource, on_delete=models.PROTECT, related_name="bookings")
    customer_name = models.CharField(max_length=255)
    customer_email = models.EmailField(blank=True)
    start_at = models.DateTimeField()
    end_at = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="confirmed")

    class Meta:
        db_table = "cycom_appointments_bookings"
        ordering = ["start_at"]

    def __str__(self):
        return f"{self.customer_name} — {self.resource} @ {self.start_at:%Y-%m-%d %H:%M}"
