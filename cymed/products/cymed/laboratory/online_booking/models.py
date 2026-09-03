"""Data models for CyMed Laboratory Online Test Booking."""
from __future__ import annotations

import uuid
from decimal import Decimal

from django.db import models
from django.utils import timezone

from platform.common.models import BaseModel


class BookableTest(BaseModel):
    tenant_id = models.UUIDField(db_index=True)
    code = models.CharField(max_length=64)
    name = models.CharField(max_length=255)
    name_ar = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=64, blank=True)
    specimen_type = models.CharField(max_length=32, blank=True)
    turnaround_hours = models.IntegerField(default=24)
    fasting_required = models.BooleanField(default=False)
    preparation_instructions = models.TextField(blank=True)
    price = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))
    currency = models.CharField(max_length=3, default="SAR")
    vat_rate = models.DecimalField(max_digits=5, decimal_places=4, default=Decimal("0.15"))
    requires_prescription = models.BooleanField(default=False)
    active = models.BooleanField(default=True)
    image_url = models.URLField(blank=True)

    class Meta:
        db_table = "cymed_lab_online_booking_bookable_test"
        unique_together = [("tenant_id", "code")]

    def __str__(self) -> str:
        return f"{self.code} — {self.name}"


class LabPackage(BaseModel):
    tenant_id = models.UUIDField(db_index=True)
    code = models.CharField(max_length=64)
    name = models.CharField(max_length=255)
    name_ar = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    tests = models.ManyToManyField(BookableTest, related_name="packages", blank=True)
    price = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))
    currency = models.CharField(max_length=3, default="SAR")
    vat_rate = models.DecimalField(max_digits=5, decimal_places=4, default=Decimal("0.15"))
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0"))
    active = models.BooleanField(default=True)
    image_url = models.URLField(blank=True)

    class Meta:
        db_table = "cymed_lab_online_booking_lab_package"
        unique_together = [("tenant_id", "code")]

    def __str__(self) -> str:
        return f"{self.code} — {self.name}"


class LabAppointmentSlot(BaseModel):
    class CollectionMode(models.TextChoices):
        IN_LAB = "in_lab", "In Lab"
        HOME = "home", "Home"
        DRIVE_THROUGH = "drive_through", "Drive Through"

    class Status(models.TextChoices):
        OPEN = "open", "Open"
        FULL = "full", "Full"
        BLOCKED = "blocked", "Blocked"
        CANCELLED = "cancelled", "Cancelled"

    tenant_id = models.UUIDField(db_index=True)
    facility_id = models.UUIDField(null=True, blank=True)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    capacity = models.IntegerField(default=1)
    booked_count = models.IntegerField(default=0)
    collection_mode = models.CharField(
        max_length=32,
        choices=CollectionMode.choices,
        default=CollectionMode.IN_LAB,
    )
    status = models.CharField(
        max_length=32,
        choices=Status.choices,
        default=Status.OPEN,
    )

    class Meta:
        db_table = "cymed_lab_online_booking_lab_appointment_slot"

    def __str__(self) -> str:
        return f"Slot {self.date} {self.start_time}-{self.end_time} ({self.collection_mode})"


class LabBooking(BaseModel):
    class PaymentStatus(models.TextChoices):
        UNPAID = "unpaid", "Unpaid"
        PAID = "paid", "Paid"
        REFUNDED = "refunded", "Refunded"
        PARTIAL_REFUND = "partial_refund", "Partial Refund"

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PLACED = "placed", "Placed"
        PAID = "paid", "Paid"
        SCHEDULED = "scheduled", "Scheduled"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    tenant_id = models.UUIDField(db_index=True)
    patient_profile_id = models.UUIDField(db_index=True)
    slot = models.ForeignKey(
        LabAppointmentSlot,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="bookings",
    )
    tests = models.JSONField(default=list, blank=True)
    packages = models.JSONField(default=list, blank=True)
    subtotal = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))
    discount = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))
    vat = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))
    total = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))
    currency = models.CharField(max_length=3, default="SAR")
    payment_status = models.CharField(
        max_length=32,
        choices=PaymentStatus.choices,
        default=PaymentStatus.UNPAID,
    )
    payment_ref = models.CharField(max_length=128, blank=True)
    bill_id = models.UUIDField(null=True, blank=True)
    order_id = models.UUIDField(null=True, blank=True)
    home_collection_booking_id = models.UUIDField(null=True, blank=True)
    status = models.CharField(
        max_length=32,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    booking_ref = models.CharField(max_length=64, blank=True)
    requisition_url = models.URLField(blank=True)

    class Meta:
        db_table = "cymed_lab_online_booking_lab_booking"

    def __str__(self) -> str:
        return f"Booking {self.booking_ref or self.id} ({self.status})"
