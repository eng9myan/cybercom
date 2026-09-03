"""Domain models for specimen chain-of-custody and courier tracking."""

from __future__ import annotations

import uuid
from decimal import Decimal

from django.db import models
from django.utils import timezone

from platform.common.models import BaseModel


class Route(BaseModel):
    class ScheduleKind(models.TextChoices):
        FIXED = "fixed", "Fixed"
        ON_DEMAND = "on_demand", "On Demand"
        HUB_AND_SPOKE = "hub_and_spoke", "Hub and Spoke"

    tenant_id = models.UUIDField(db_index=True)
    code = models.CharField(max_length=64)
    name = models.CharField(max_length=128)
    origin_facility_id = models.UUIDField(null=True, blank=True)
    destination_facility_id = models.UUIDField(null=True, blank=True)
    schedule_kind = models.CharField(max_length=32, choices=ScheduleKind.choices, default=ScheduleKind.FIXED)
    active = models.BooleanField(default=True)

    class Meta:
        db_table = "cymed_lab_courier_tracking_route"
        unique_together = [("tenant_id", "code")]

    def __str__(self) -> str:
        return f"{self.code} — {self.name}"


class Run(BaseModel):
    class Status(models.TextChoices):
        PLANNED = "planned", "Planned"
        IN_PROGRESS = "in_progress", "In Progress"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    tenant_id = models.UUIDField(db_index=True)
    route = models.ForeignKey(Route, on_delete=models.PROTECT, related_name="runs")
    run_date = models.DateField()
    driver_id = models.UUIDField(null=True, blank=True)
    vehicle_plate = models.CharField(max_length=32, blank=True)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.PLANNED)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    cold_chain = models.BooleanField(default=False)

    class Meta:
        db_table = "cymed_lab_courier_tracking_run"

    def __str__(self) -> str:
        return f"Run {self.route_id} {self.run_date} [{self.status}]"


class ChainOfCustodyEvent(BaseModel):
    class Kind(models.TextChoices):
        COLLECTED = "collected", "Collected"
        HANDED_TO_COURIER = "handed_to_courier", "Handed to Courier"
        IN_TRANSIT = "in_transit", "In Transit"
        ARRIVED_AT_HUB = "arrived_at_hub", "Arrived at Hub"
        DEPARTED_HUB = "departed_hub", "Departed Hub"
        DELIVERED_TO_LAB = "delivered_to_lab", "Delivered to Lab"
        ACCESSIONED = "accessioned", "Accessioned"
        REJECTED = "rejected", "Rejected"
        LOST = "lost", "Lost"

    tenant_id = models.UUIDField(db_index=True)
    specimen_barcode = models.CharField(max_length=64, db_index=True)
    order_id = models.UUIDField(null=True, blank=True)
    run = models.ForeignKey(Run, on_delete=models.SET_NULL, null=True, blank=True, related_name="custody_events")
    at = models.DateTimeField(default=timezone.now)
    kind = models.CharField(max_length=32, choices=Kind.choices)
    actor_profile_id = models.UUIDField(null=True, blank=True)
    lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    lng = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    temperature_c = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    signature_url = models.URLField(blank=True)
    note = models.TextField(blank=True)

    class Meta:
        db_table = "cymed_lab_courier_tracking_chain_of_custody_event"

    def __str__(self) -> str:
        return f"{self.specimen_barcode} — {self.kind} @ {self.at.isoformat()}"


class TransportTemperature(BaseModel):
    run = models.ForeignKey(Run, on_delete=models.CASCADE, related_name="temperatures")
    specimen_barcode = models.CharField(max_length=64, db_index=True)
    at = models.DateTimeField(default=timezone.now)
    temperature_c = models.DecimalField(max_digits=6, decimal_places=2)
    breach = models.BooleanField(default=False)

    class Meta:
        db_table = "cymed_lab_courier_tracking_transport_temperature"

    def __str__(self) -> str:
        return f"{self.specimen_barcode} {self.temperature_c}C breach={self.breach}"


class Manifest(BaseModel):
    tenant_id = models.UUIDField(db_index=True)
    run = models.ForeignKey(Run, on_delete=models.PROTECT, related_name="manifests")
    generated_at = models.DateTimeField(default=timezone.now)
    specimen_barcodes = models.JSONField(default=list, blank=True)
    total_specimens = models.IntegerField(default=0)
    driver_signature_url = models.URLField(blank=True)
    receiver_signature_url = models.URLField(blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "cymed_lab_courier_tracking_manifest"

    def __str__(self) -> str:
        return f"Manifest run={self.run_id} total={self.total_specimens}"
