"""Domain models for phlebotomist home-visit sample collection."""

from __future__ import annotations

import uuid
from decimal import Decimal

from django.db import models
from django.utils import timezone

from platform.common.models import BaseModel


class Phlebotomist(BaseModel):
    class Meta:
        db_table = "cymed_lab_home_collection_phlebotomist"

    tenant_id = models.UUIDField(db_index=True)
    user_profile_id = models.UUIDField(db_index=True)
    first_name = models.CharField(max_length=128)
    last_name = models.CharField(max_length=128)
    phone = models.CharField(max_length=32)
    license_number = models.CharField(max_length=64, blank=True)
    vehicle_plate = models.CharField(max_length=32, blank=True)
    active = models.BooleanField(default=True)
    coverage_cities = models.JSONField(default=list, blank=True)
    cold_chain_capable = models.BooleanField(default=False)
    current_lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    current_lng = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    location_updated_at = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name}"


class HomeCollectionSlot(BaseModel):
    class Status(models.TextChoices):
        OPEN = "open", "Open"
        FULL = "full", "Full"
        BLOCKED = "blocked", "Blocked"
        CANCELLED = "cancelled", "Cancelled"

    class Meta:
        db_table = "cymed_lab_home_collection_homecollectionslot"

    tenant_id = models.UUIDField(db_index=True)
    phlebotomist = models.ForeignKey(
        Phlebotomist,
        on_delete=models.CASCADE,
        related_name="slots",
    )
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    capacity = models.IntegerField(default=1)
    booked_count = models.IntegerField(default=0)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.OPEN)

    def __str__(self) -> str:
        return f"Slot {self.date} {self.start_time}-{self.end_time}"


class HomeCollectionBooking(BaseModel):
    class Status(models.TextChoices):
        REQUESTED = "requested", "Requested"
        CONFIRMED = "confirmed", "Confirmed"
        DISPATCHED = "dispatched", "Dispatched"
        EN_ROUTE = "en_route", "En Route"
        ARRIVED = "arrived", "Arrived"
        COLLECTED = "collected", "Collected"
        DELIVERED_TO_LAB = "delivered_to_lab", "Delivered To Lab"
        CANCELLED = "cancelled", "Cancelled"
        NO_SHOW = "no_show", "No Show"

    class PaymentStatus(models.TextChoices):
        UNPAID = "unpaid", "Unpaid"
        PAID = "paid", "Paid"
        REFUNDED = "refunded", "Refunded"

    class Meta:
        db_table = "cymed_lab_home_collection_homecollectionbooking"

    tenant_id = models.UUIDField(db_index=True)
    patient_profile_id = models.UUIDField(db_index=True)
    order_id = models.UUIDField(null=True, blank=True)
    slot = models.ForeignKey(
        HomeCollectionSlot,
        on_delete=models.PROTECT,
        related_name="bookings",
    )
    phlebotomist = models.ForeignKey(
        Phlebotomist,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="bookings",
    )
    address = models.JSONField(default=dict, blank=True)
    lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    lng = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    tests_requested = models.JSONField(default=list, blank=True)
    fasting_required = models.BooleanField(default=False)
    special_instructions = models.TextField(blank=True)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.REQUESTED)
    payment_status = models.CharField(
        max_length=32,
        choices=PaymentStatus.choices,
        default=PaymentStatus.UNPAID,
    )
    payment_ref = models.CharField(max_length=128, blank=True)
    estimated_arrival = models.DateTimeField(null=True, blank=True)
    collection_started_at = models.DateTimeField(null=True, blank=True)
    collection_completed_at = models.DateTimeField(null=True, blank=True)
    specimen_barcodes = models.JSONField(default=list, blank=True)
    proof_of_collection = models.JSONField(default=dict, blank=True)

    def __str__(self) -> str:
        return f"Booking {self.id} ({self.status})"


class HomeCollectionEvent(BaseModel):
    class Kind(models.TextChoices):
        CREATED = "created", "Created"
        ASSIGNED = "assigned", "Assigned"
        DISPATCHED = "dispatched", "Dispatched"
        ARRIVED = "arrived", "Arrived"
        COLLECTED = "collected", "Collected"
        DELIVERED = "delivered", "Delivered"
        CANCELLED = "cancelled", "Cancelled"
        RESCHEDULED = "rescheduled", "Rescheduled"
        CUSTOMER_ABSENT = "customer_absent", "Customer Absent"

    class Meta:
        db_table = "cymed_lab_home_collection_homecollectionevent"

    booking = models.ForeignKey(
        HomeCollectionBooking,
        on_delete=models.CASCADE,
        related_name="events",
    )
    at = models.DateTimeField(default=timezone.now)
    kind = models.CharField(max_length=32, choices=Kind.choices)
    lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    lng = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    note = models.TextField(blank=True)

    def __str__(self) -> str:
        return f"Event {self.kind} @ {self.at}"
