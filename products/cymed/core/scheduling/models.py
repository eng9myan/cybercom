from django.db import models
from platform.common.models import BaseModel
from products.cymed.core.patients.models import Patient
from products.cymed.core.providers.models import Provider

class AppointmentStatus(models.TextChoices):
    PROPOSED = "proposed", "Proposed"
    PENDING = "pending", "Pending"
    BOOKED = "booked", "Booked"
    ARRIVED = "arrived", "Arrived"
    FULFILLED = "fulfilled", "Fulfilled"
    CANCELLED = "cancelled", "Cancelled"

class AppointmentParticipantType(models.TextChoices):
    PATIENT = "patient", "Patient"
    PROVIDER = "provider", "Provider"
    LOCATION = "location", "Location"

class Appointment(BaseModel):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="appointments")
    appointment_type = models.CharField(max_length=100)  # e.g., "follow-up", "checkup"
    status = models.CharField(max_length=30, choices=AppointmentStatus.choices, default=AppointmentStatus.BOOKED)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    description = models.TextField(blank=True)

    class Meta:
        db_table = "cymed_appointments"
        ordering = ["start_time"]

    def __str__(self) -> str:
        return f"Appointment({self.patient.mrn}, {self.start_time}, {self.status})"


class AppointmentParticipant(BaseModel):
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name="participants")
    actor_id = models.UUIDField()  # maps to Patient, Provider, or Bed/Room ID
    actor_type = models.CharField(max_length=30, choices=AppointmentParticipantType.choices)
    required = models.BooleanField(default=True)
    status = models.CharField(max_length=30, choices=[
        ("accepted", "Accepted"), ("declined", "Declined"),
        ("tentative", "Tentative"), ("needs_action", "Needs Action")
    ], default="needs_action")

    class Meta:
        db_table = "cymed_appointment_participants"


class ResourceSchedule(BaseModel):
    resource_id = models.UUIDField()
    resource_type = models.CharField(max_length=100)  # e.g., "room", "machine"
    name = models.CharField(max_length=255)

    class Meta:
        db_table = "cymed_resource_schedules"


class ScheduleSlot(BaseModel):
    resource_id = models.UUIDField(db_index=True)  # maps to Provider or Resource ID
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    status = models.CharField(max_length=30, choices=[
        ("free", "Free"), ("busy", "Busy"), ("tentative", "Tentative")
    ], default="free")

    class Meta:
        db_table = "cymed_schedule_slots"
        ordering = ["start_time"]
