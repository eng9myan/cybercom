"""CyMed Pharmacy robotics models."""
from __future__ import annotations

import uuid
from decimal import Decimal

from django.db import models
from django.utils import timezone

from platform.common.models import BaseModel


class RobotDevice(BaseModel):
    class Vendor(models.TextChoices):
        PYXIS = "pyxis", "Pyxis"
        OMNICELL = "omnicell", "Omnicell"
        PARATA = "parata", "Parata"
        MEDITECH = "meditech", "Meditech"
        KIRBY_LESTER = "kirby_lester", "Kirby-Lester"
        GENERIC = "generic", "Generic"

    class Protocol(models.TextChoices):
        HTTP_JSON = "http_json", "HTTP JSON"
        HL7 = "hl7", "HL7"
        VENDOR_SDK = "vendor_sdk", "Vendor SDK"
        MANUAL = "manual", "Manual"

    class Status(models.TextChoices):
        ONLINE = "online", "Online"
        OFFLINE = "offline", "Offline"
        ERROR = "error", "Error"
        MAINTENANCE = "maintenance", "Maintenance"

    tenant_id = models.UUIDField(db_index=True)
    code = models.CharField(max_length=64)
    vendor = models.CharField(max_length=32, choices=Vendor.choices)
    model_name = models.CharField(max_length=128, blank=True)
    location_label = models.CharField(max_length=128, blank=True)
    facility_id = models.UUIDField(null=True, blank=True)
    ip_address = models.CharField(max_length=64, blank=True)
    api_endpoint = models.URLField(blank=True)
    protocol = models.CharField(max_length=32, choices=Protocol.choices, default=Protocol.HTTP_JSON)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.OFFLINE)
    last_heartbeat_at = models.DateTimeField(null=True, blank=True)
    capabilities = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "cymed_pharmacy_robotics_robot_device"
        unique_together = [("tenant_id", "code")]

    def __str__(self) -> str:
        return f"{self.code} ({self.vendor})"


class RobotBinInventory(BaseModel):
    device = models.ForeignKey(RobotDevice, on_delete=models.CASCADE, related_name="bins")
    bin_code = models.CharField(max_length=32)
    drug_id = models.UUIDField(null=True, blank=True)
    drug_name = models.CharField(max_length=255)
    ndc = models.CharField(max_length=32, blank=True)
    lot_number = models.CharField(max_length=64, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    qty_on_hand = models.IntegerField(default=0)
    par_level = models.IntegerField(default=0)
    last_counted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "cymed_pharmacy_robotics_robot_bin_inventory"

    def __str__(self) -> str:
        return f"{self.device_id}:{self.bin_code} {self.drug_name}"


class DispenseJob(BaseModel):
    class Status(models.TextChoices):
        QUEUED = "queued", "Queued"
        DISPATCHED = "dispatched", "Dispatched"
        DISPENSING = "dispensing", "Dispensing"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"
        CANCELLED = "cancelled", "Cancelled"

    tenant_id = models.UUIDField(db_index=True)
    device = models.ForeignKey(RobotDevice, on_delete=models.CASCADE, related_name="jobs")
    order_id = models.UUIDField(db_index=True)
    patient_profile_id = models.UUIDField(null=True, blank=True)
    drug_id = models.UUIDField(null=True, blank=True)
    drug_name = models.CharField(max_length=255)
    qty_requested = models.IntegerField()
    qty_dispensed = models.IntegerField(default=0)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.QUEUED)
    lot_number = models.CharField(max_length=64, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    vendor_reference = models.CharField(max_length=128, blank=True)
    dispatched_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "cymed_pharmacy_robotics_dispense_job"

    def __str__(self) -> str:
        return f"DispenseJob {self.pk} {self.drug_name} x{self.qty_requested}"


class RobotEvent(BaseModel):
    class Kind(models.TextChoices):
        HEARTBEAT = "heartbeat", "Heartbeat"
        DISPENSE_OK = "dispense_ok", "Dispense OK"
        DISPENSE_FAIL = "dispense_fail", "Dispense Fail"
        LOW_STOCK = "low_stock", "Low Stock"
        EXPIRY_WARN = "expiry_warn", "Expiry Warn"
        RESTOCK = "restock", "Restock"
        MAINTENANCE = "maintenance", "Maintenance"

    device = models.ForeignKey(RobotDevice, on_delete=models.CASCADE, related_name="events")
    at = models.DateTimeField(default=timezone.now)
    kind = models.CharField(max_length=32, choices=Kind.choices)
    payload = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "cymed_pharmacy_robotics_robot_event"

    def __str__(self) -> str:
        return f"{self.kind}@{self.device_id} {self.at:%Y-%m-%d %H:%M:%S}"
