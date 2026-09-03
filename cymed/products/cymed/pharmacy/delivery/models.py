"""CyMed Pharmacy Delivery models."""
from __future__ import annotations

import uuid
from decimal import Decimal

from django.db import models
from django.utils import timezone

from platform.common.models import BaseModel


class Courier(BaseModel):
    class Provider(models.TextChoices):
        INTERNAL = "internal", "Internal"
        ARAMEX = "aramex", "Aramex"
        DHL = "dhl", "DHL"
        NAQEL = "naqel", "Naqel"
        SMSA = "smsa", "SMSA"
        MRSOOL = "mrsool", "Mrsool"
        CAREEM = "careem", "Careem"
        OTHER = "other", "Other"

    tenant_id = models.UUIDField(db_index=True)
    name = models.CharField(max_length=255)
    provider = models.CharField(max_length=32, choices=Provider.choices, default=Provider.INTERNAL)
    api_key = models.CharField(max_length=255, blank=True)
    api_endpoint = models.URLField(blank=True)
    active = models.BooleanField(default=True)
    coverage_areas = models.JSONField(default=list, blank=True)
    cold_chain_capable = models.BooleanField(default=False)

    class Meta:
        db_table = "cymed_pharmacy_delivery_courier"

    def __str__(self) -> str:
        return f"{self.name} ({self.provider})"


class Rider(BaseModel):
    class VehicleType(models.TextChoices):
        MOTORBIKE = "motorbike", "Motorbike"
        CAR = "car", "Car"
        VAN = "van", "Van"
        BICYCLE = "bicycle", "Bicycle"

    tenant_id = models.UUIDField(db_index=True)
    courier = models.ForeignKey(Courier, on_delete=models.CASCADE, related_name="riders")
    external_id = models.CharField(max_length=128)
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=32)
    vehicle_type = models.CharField(max_length=32, choices=VehicleType.choices, default=VehicleType.MOTORBIKE)
    active = models.BooleanField(default=True)
    current_lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    current_lng = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    location_updated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "cymed_pharmacy_delivery_rider"

    def __str__(self) -> str:
        return f"{self.name} [{self.external_id}]"


class DeliveryJob(BaseModel):
    class Status(models.TextChoices):
        CREATED = "created", "Created"
        ASSIGNED = "assigned", "Assigned"
        PICKED_UP = "picked_up", "Picked Up"
        IN_TRANSIT = "in_transit", "In Transit"
        DELIVERED = "delivered", "Delivered"
        FAILED = "failed", "Failed"
        RETURNED = "returned", "Returned"
        CANCELLED = "cancelled", "Cancelled"

    tenant_id = models.UUIDField(db_index=True)
    order_id = models.UUIDField(db_index=True)
    patient_profile_id = models.UUIDField(db_index=True)
    courier = models.ForeignKey(Courier, on_delete=models.PROTECT, related_name="jobs")
    rider = models.ForeignKey(Rider, on_delete=models.SET_NULL, null=True, blank=True, related_name="jobs")
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.CREATED)
    pickup_address = models.JSONField(default=dict, blank=True)
    drop_address = models.JSONField(default=dict, blank=True)
    pickup_lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    pickup_lng = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    drop_lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    drop_lng = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    requested_slot_start = models.DateTimeField(null=True, blank=True)
    requested_slot_end = models.DateTimeField(null=True, blank=True)
    estimated_arrival = models.DateTimeField(null=True, blank=True)
    cold_chain_required = models.BooleanField(default=False)
    proof_of_delivery = models.JSONField(default=dict, blank=True)
    failure_reason = models.TextField(blank=True)
    courier_tracking_id = models.CharField(max_length=128, blank=True)
    cost = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))

    class Meta:
        db_table = "cymed_pharmacy_delivery_delivery_job"

    def __str__(self) -> str:
        return f"DeliveryJob {self.pk} [{self.status}]"


class DeliveryStatusEvent(BaseModel):
    job = models.ForeignKey(DeliveryJob, on_delete=models.CASCADE, related_name="events")
    at = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=32)
    lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    lng = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    note = models.TextField(blank=True)

    class Meta:
        db_table = "cymed_pharmacy_delivery_delivery_status_event"

    def __str__(self) -> str:
        return f"Event {self.status} @ {self.at}"
