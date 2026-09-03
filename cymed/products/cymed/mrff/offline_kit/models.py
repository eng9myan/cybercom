"""Data models for CyMed MRFF offline-first rural kit sub-app."""
from __future__ import annotations

import uuid
from decimal import Decimal

from django.db import models
from django.utils import timezone

from platform.common.models import BaseModel


class OfflineDevice(BaseModel):
    class DeviceKind(models.TextChoices):
        TABLET = "tablet", "Tablet"
        LAPTOP = "laptop", "Laptop"
        PHONE = "phone", "Phone"
        KIOSK = "kiosk", "Kiosk"
        MOBILE_CLINIC_VAN = "mobile_clinic_van", "Mobile Clinic Van"

    tenant_id = models.UUIDField(db_index=True)
    device_uuid = models.CharField(max_length=64, unique=True)
    device_kind = models.CharField(max_length=32, choices=DeviceKind.choices)
    operator_profile_id = models.UUIDField(null=True, blank=True)
    facility_id = models.UUIDField(null=True, blank=True)
    accho_flag = models.BooleanField(default=False)
    last_sync_at = models.DateTimeField(null=True, blank=True)
    storage_used_mb = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    app_version = models.CharField(max_length=32, blank=True)
    platform = models.CharField(max_length=32, blank=True)
    active = models.BooleanField(default=True)

    class Meta:
        db_table = "cymed_mrff_offline_kit_offline_device"

    def __str__(self) -> str:
        return f"OfflineDevice({self.device_uuid}, {self.device_kind})"


class OfflineIntake(BaseModel):
    class EncounterKind(models.TextChoices):
        ROUTINE = "routine", "Routine"
        URGENT = "urgent", "Urgent"
        EMERGENCY = "emergency", "Emergency"
        OUTREACH_VISIT = "outreach_visit", "Outreach Visit"
        FOLLOW_UP = "follow_up", "Follow Up"

    class SyncStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        SYNCED = "synced", "Synced"
        CONFLICTED = "conflicted", "Conflicted"
        REJECTED = "rejected", "Rejected"

    tenant_id = models.UUIDField(db_index=True)
    device = models.ForeignKey(OfflineDevice, on_delete=models.CASCADE, related_name="intakes")
    local_id = models.CharField(max_length=64)
    patient_profile_id = models.UUIDField(null=True, blank=True)
    patient_snapshot = models.JSONField(default=dict)
    chief_complaint = models.TextField(blank=True)
    vitals = models.JSONField(default=dict)
    history = models.JSONField(default=list)
    cdss_alerts = models.JSONField(default=list)
    encounter_kind = models.CharField(max_length=32, choices=EncounterKind.choices, default=EncounterKind.ROUTINE)
    captured_at = models.DateTimeField(default=timezone.now)
    accho_specific = models.JSONField(default=dict)
    sync_status = models.CharField(max_length=32, choices=SyncStatus.choices, default=SyncStatus.PENDING)
    sync_error = models.TextField(blank=True)
    synced_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "cymed_mrff_offline_kit_offline_intake"
        unique_together = [("device", "local_id")]

    def __str__(self) -> str:
        return f"OfflineIntake({self.local_id}, {self.sync_status})"


class SyncQueueItem(BaseModel):
    class PayloadKind(models.TextChoices):
        INTAKE = "intake", "Intake"
        VITALS = "vitals", "Vitals"
        LAB_RESULT = "lab_result", "Lab Result"
        PRESCRIPTION = "prescription", "Prescription"
        CONSENT = "consent", "Consent"
        NOTE = "note", "Note"
        ATTACHMENT = "attachment", "Attachment"

    class Status(models.TextChoices):
        QUEUED = "queued", "Queued"
        IN_PROGRESS = "in_progress", "In Progress"
        SENT = "sent", "Sent"
        FAILED = "failed", "Failed"
        CONFLICT = "conflict", "Conflict"
        SUPERSEDED = "superseded", "Superseded"

    tenant_id = models.UUIDField(db_index=True)
    device = models.ForeignKey(OfflineDevice, on_delete=models.CASCADE, related_name="queue_items")
    payload_kind = models.CharField(max_length=32, choices=PayloadKind.choices)
    local_ref = models.CharField(max_length=64)
    payload = models.JSONField(default=dict)
    created_at = models.DateTimeField(default=timezone.now)
    attempted_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.QUEUED)
    error_message = models.TextField(blank=True)
    attempts = models.IntegerField(default=0)
    server_id = models.UUIDField(null=True, blank=True)

    class Meta:
        db_table = "cymed_mrff_offline_kit_sync_queue_item"

    def __str__(self) -> str:
        return f"SyncQueueItem({self.payload_kind}, {self.status})"


class ConflictResolution(BaseModel):
    class Strategy(models.TextChoices):
        SERVER_WINS = "server_wins", "Server Wins"
        CLIENT_WINS = "client_wins", "Client Wins"
        MERGE = "merge", "Merge"
        MANUAL = "manual", "Manual"

    queue_item = models.ForeignKey(SyncQueueItem, on_delete=models.CASCADE, related_name="conflict_resolutions")
    server_snapshot = models.JSONField(default=dict)
    client_snapshot = models.JSONField(default=dict)
    strategy = models.CharField(max_length=32, choices=Strategy.choices, default=Strategy.MANUAL)
    resolved_by_profile_id = models.UUIDField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_payload = models.JSONField(default=dict)

    class Meta:
        db_table = "cymed_mrff_offline_kit_conflict_resolution"

    def __str__(self) -> str:
        return f"ConflictResolution({self.queue_item_id}, {self.strategy})"


class OfflineCdssRun(BaseModel):
    class Kind(models.TextChoices):
        QSOFA = "qsofa", "qSOFA"
        NEWS2 = "news2", "NEWS2"
        LACE = "lace", "LACE"
        MORSE = "morse", "Morse"
        PEDS_ASTHMA = "peds_asthma", "Pediatric Asthma"
        RED_FLAG_SCREEN = "red_flag_screen", "Red Flag Screen"
        OTTAWA_ANKLE = "ottawa_ankle", "Ottawa Ankle"
        CAGE = "cage", "CAGE"
        AUSDRISK = "ausdrisk", "AUSDRISK"

    class Band(models.TextChoices):
        LOW = "low", "Low"
        MODERATE = "moderate", "Moderate"
        HIGH = "high", "High"
        CRITICAL = "critical", "Critical"
        N_A = "n_a", "N/A"

    intake = models.ForeignKey(OfflineIntake, on_delete=models.CASCADE, related_name="cdss_runs")
    kind = models.CharField(max_length=32, choices=Kind.choices)
    score = models.DecimalField(max_digits=9, decimal_places=4)
    band = models.CharField(max_length=32, choices=Band.choices, default=Band.N_A)
    recommendations = models.JSONField(default=list)
    computed_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "cymed_mrff_offline_kit_offline_cdss_run"

    def __str__(self) -> str:
        return f"OfflineCdssRun({self.kind}, {self.band})"
