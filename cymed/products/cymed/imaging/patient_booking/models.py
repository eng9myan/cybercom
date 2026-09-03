"""Domain models for CyMed Imaging patient booking."""

from __future__ import annotations

import uuid
from decimal import Decimal

from django.db import models
from django.utils import timezone

from platform.common.models import BaseModel


class BookableStudy(BaseModel):
    class Modality(models.TextChoices):
        XRAY = "xray", "X-Ray"
        CT = "ct", "CT"
        MRI = "mri", "MRI"
        US = "us", "Ultrasound"
        MAMMO = "mammo", "Mammography"
        FLUORO = "fluoro", "Fluoroscopy"
        NUCMED = "nucmed", "Nuclear Medicine"
        PET = "pet", "PET"
        DEXA = "dexa", "DEXA"
        DENTAL = "dental", "Dental"

    tenant_id = models.UUIDField(db_index=True)
    code = models.CharField(max_length=64)
    name = models.CharField(max_length=255)
    name_ar = models.CharField(max_length=255, blank=True)
    modality = models.CharField(max_length=32, choices=Modality.choices)
    body_part = models.CharField(max_length=64, blank=True)
    contrast_required = models.BooleanField(default=False)
    duration_minutes = models.IntegerField(default=15)
    preparation_instructions = models.TextField(blank=True)
    price = models.DecimalField(max_digits=18, decimal_places=4)
    currency = models.CharField(max_length=3, default="SAR")
    vat_rate = models.DecimalField(max_digits=5, decimal_places=4, default=Decimal("0.15"))
    requires_referral = models.BooleanField(default=False)
    active = models.BooleanField(default=True)
    image_url = models.URLField(blank=True)

    class Meta:
        db_table = "cymed_img_patient_booking_bookable_study"
        unique_together = [("tenant_id", "code")]

    def __str__(self) -> str:
        return f"{self.code} — {self.name}"


class ModalityRoom(BaseModel):
    class Modality(models.TextChoices):
        XRAY = "xray", "X-Ray"
        CT = "ct", "CT"
        MRI = "mri", "MRI"
        US = "us", "Ultrasound"
        MAMMO = "mammo", "Mammography"
        FLUORO = "fluoro", "Fluoroscopy"
        NUCMED = "nucmed", "Nuclear Medicine"
        PET = "pet", "PET"
        DEXA = "dexa", "DEXA"
        DENTAL = "dental", "Dental"

    tenant_id = models.UUIDField(db_index=True)
    facility_id = models.UUIDField(null=True, blank=True)
    code = models.CharField(max_length=64)
    name = models.CharField(max_length=128)
    modality = models.CharField(max_length=32, choices=Modality.choices)
    manufacturer = models.CharField(max_length=64, blank=True)
    model_name = models.CharField(max_length=64, blank=True)
    ae_title = models.CharField(max_length=32, blank=True)
    active = models.BooleanField(default=True)

    class Meta:
        db_table = "cymed_img_patient_booking_modality_room"
        unique_together = [("tenant_id", "code")]

    def __str__(self) -> str:
        return f"{self.code} — {self.name}"


class ImagingSlot(BaseModel):
    class Status(models.TextChoices):
        OPEN = "open", "Open"
        FULL = "full", "Full"
        BLOCKED = "blocked", "Blocked"
        CANCELLED = "cancelled", "Cancelled"

    tenant_id = models.UUIDField(db_index=True)
    room = models.ForeignKey(ModalityRoom, on_delete=models.PROTECT, related_name="slots")
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    capacity = models.IntegerField(default=1)
    booked_count = models.IntegerField(default=0)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.OPEN)

    class Meta:
        db_table = "cymed_img_patient_booking_imaging_slot"

    def __str__(self) -> str:
        return f"Slot {self.room_id} {self.date} {self.start_time}-{self.end_time}"


class ImagingBooking(BaseModel):
    class PaymentStatus(models.TextChoices):
        UNPAID = "unpaid", "Unpaid"
        PAID = "paid", "Paid"
        REFUNDED = "refunded", "Refunded"

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PLACED = "placed", "Placed"
        PAID = "paid", "Paid"
        SCHEDULED = "scheduled", "Scheduled"
        ARRIVED = "arrived", "Arrived"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"
        NO_SHOW = "no_show", "No Show"

    tenant_id = models.UUIDField(db_index=True)
    patient_profile_id = models.UUIDField(db_index=True)
    study = models.ForeignKey(BookableStudy, on_delete=models.PROTECT, related_name="bookings")
    slot = models.ForeignKey(
        ImagingSlot,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="bookings",
    )
    referral_url = models.URLField(blank=True)
    referring_provider_id = models.UUIDField(null=True, blank=True)
    payment_status = models.CharField(
        max_length=32,
        choices=PaymentStatus.choices,
        default=PaymentStatus.UNPAID,
    )
    payment_ref = models.CharField(max_length=128, blank=True)
    bill_id = models.UUIDField(null=True, blank=True)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.DRAFT)
    booking_ref = models.CharField(max_length=64, blank=True)
    preparation_confirmed = models.BooleanField(default=False)
    fasting_confirmed = models.BooleanField(default=False)
    consent_signed_at = models.DateTimeField(null=True, blank=True)
    order_id = models.UUIDField(null=True, blank=True)

    class Meta:
        db_table = "cymed_img_patient_booking_imaging_booking"

    def __str__(self) -> str:
        return f"Booking {self.booking_ref or self.pk}"
