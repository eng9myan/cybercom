"""Domain models for cross-tenant shared inventory, capacity, and provider pools."""
from __future__ import annotations

import uuid
from decimal import Decimal

from django.db import models
from django.utils import timezone

from platform.common.models import BaseModel


class ResourceOffer(BaseModel):
    class Kind(models.TextChoices):
        DRUG_STOCK = "drug_stock", "Drug Stock"
        LAB_CAPACITY = "lab_capacity", "Lab Capacity"
        RADIOLOGIST_SHIFT = "radiologist_shift", "Radiologist Shift"
        IMAGING_SLOT = "imaging_slot", "Imaging Slot"
        OR_BLOCK = "or_block", "OR Block"
        HOSPITAL_BED = "hospital_bed", "Hospital Bed"
        PHLEBOTOMIST = "phlebotomist", "Phlebotomist"

    class Status(models.TextChoices):
        OPEN = "open", "Open"
        RESERVED = "reserved", "Reserved"
        PARTIALLY_TAKEN = "partially_taken", "Partially Taken"
        CLOSED = "closed", "Closed"
        EXPIRED = "expired", "Expired"

    kind = models.CharField(max_length=32, choices=Kind.choices)
    code = models.CharField(max_length=64, blank=True)
    description = models.CharField(max_length=255, blank=True)
    quantity = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))
    uom = models.CharField(max_length=16, blank=True)
    start_at = models.DateTimeField(null=True, blank=True)
    end_at = models.DateTimeField(null=True, blank=True)
    location = models.JSONField(default=dict, blank=True)
    price_per_unit = models.DecimalField(max_digits=18, decimal_places=4, null=True, blank=True)
    currency = models.CharField(max_length=3, default="SAR")
    tags = models.JSONField(default=list, blank=True)
    visible_to_tenant_ids = models.JSONField(default=list, blank=True)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.OPEN)
    posted_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "cymed_eco_shared_capacity_resource_offer"

    def __str__(self) -> str:
        return f"ResourceOffer<{self.kind} {self.code} qty={self.quantity}>"


class ResourceRequest(BaseModel):
    class Kind(models.TextChoices):
        DRUG_STOCK = "drug_stock", "Drug Stock"
        LAB_CAPACITY = "lab_capacity", "Lab Capacity"
        RADIOLOGIST_SHIFT = "radiologist_shift", "Radiologist Shift"
        IMAGING_SLOT = "imaging_slot", "Imaging Slot"
        OR_BLOCK = "or_block", "OR Block"
        HOSPITAL_BED = "hospital_bed", "Hospital Bed"
        PHLEBOTOMIST = "phlebotomist", "Phlebotomist"

    class Urgency(models.TextChoices):
        ROUTINE = "routine", "Routine"
        URGENT = "urgent", "Urgent"
        CRITICAL = "critical", "Critical"

    class Status(models.TextChoices):
        OPEN = "open", "Open"
        MATCHED = "matched", "Matched"
        FULFILLED = "fulfilled", "Fulfilled"
        EXPIRED = "expired", "Expired"
        CANCELLED = "cancelled", "Cancelled"

    kind = models.CharField(max_length=32, choices=Kind.choices)
    code = models.CharField(max_length=64, blank=True)
    description = models.CharField(max_length=255, blank=True)
    quantity_needed = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))
    uom = models.CharField(max_length=16, blank=True)
    needed_by = models.DateTimeField(null=True, blank=True)
    max_price_per_unit = models.DecimalField(max_digits=18, decimal_places=4, null=True, blank=True)
    currency = models.CharField(max_length=3, default="SAR")
    location = models.JSONField(default=dict, blank=True)
    urgency = models.CharField(max_length=32, choices=Urgency.choices, default=Urgency.ROUTINE)
    matched_offer = models.ForeignKey(
        ResourceOffer,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="requests",
    )
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.OPEN)
    posted_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "cymed_eco_shared_capacity_resource_request"

    def __str__(self) -> str:
        return f"ResourceRequest<{self.kind} {self.code} qty={self.quantity_needed}>"


class ResourceMatch(BaseModel):
    class Status(models.TextChoices):
        PROPOSED = "proposed", "Proposed"
        ACCEPTED = "accepted", "Accepted"
        DECLINED = "declined", "Declined"
        FULFILLED = "fulfilled", "Fulfilled"
        CANCELLED = "cancelled", "Cancelled"

    offer = models.ForeignKey(ResourceOffer, on_delete=models.CASCADE, related_name="matches")
    request = models.ForeignKey(ResourceRequest, on_delete=models.CASCADE, related_name="matches")
    quantity = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))
    agreed_price_per_unit = models.DecimalField(max_digits=18, decimal_places=4, null=True, blank=True)
    currency = models.CharField(max_length=3, default="SAR")
    total_amount = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.PROPOSED)
    created_at_ts = models.DateTimeField(default=timezone.now)
    accepted_at = models.DateTimeField(null=True, blank=True)
    fulfilled_at = models.DateTimeField(null=True, blank=True)
    decline_reason = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "cymed_eco_shared_capacity_resource_match"

    def __str__(self) -> str:
        return f"ResourceMatch<offer={self.offer_id} request={self.request_id} qty={self.quantity}>"


class RadiologistPoolShift(BaseModel):
    class Status(models.TextChoices):
        OPEN = "open", "Open"
        PARTIALLY_FULL = "partially_full", "Partially Full"
        FULL = "full", "Full"
        CLOSED = "closed", "Closed"

    tenant_id = models.UUIDField(null=True, blank=True, db_index=True)
    provider_id = models.UUIDField(null=True, blank=True)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    modalities = models.JSONField(default=list, blank=True)
    max_studies = models.IntegerField(default=0)
    accepted_studies = models.IntegerField(default=0)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.OPEN)

    class Meta:
        db_table = "cymed_eco_shared_capacity_radiologist_pool_shift"

    def __str__(self) -> str:
        return f"RadiologistPoolShift<{self.date} {self.start_time}-{self.end_time}>"
