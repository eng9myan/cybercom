"""
Hospital Clinical Command Center — Domain Models.
Real-time operational awareness: census, capacity, staffing, quality, safety.
"""
from django.db import models
from platform.common.models import BaseModel


class AlertSeverity(models.TextChoices):
    CRITICAL = "critical", "Critical"
    HIGH = "high", "High"
    MEDIUM = "medium", "Medium"
    LOW = "low", "Low"
    INFO = "info", "Info"


class AlertStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    ACKNOWLEDGED = "acknowledged", "Acknowledged"
    ESCALATED = "escalated", "Escalated"
    RESOLVED = "resolved", "Resolved"


class CapacityStatus(models.TextChoices):
    NORMAL = "normal", "Normal"
    ELEVATED = "elevated", "Elevated"
    HIGH = "high", "High"
    CRITICAL = "critical", "Critical"
    DIVERSION = "diversion", "Diversion"


class CommandCenterSnapshot(BaseModel):
    """Periodic operational snapshot — persisted for trending and reporting."""
    snapshot_time = models.DateTimeField(auto_now_add=True, db_index=True)
    total_beds = models.PositiveIntegerField(default=0)
    occupied_beds = models.PositiveIntegerField(default=0)
    available_beds = models.PositiveIntegerField(default=0)
    icu_total = models.PositiveIntegerField(default=0)
    icu_occupied = models.PositiveIntegerField(default=0)
    ed_visits_active = models.PositiveIntegerField(default=0)
    ed_waiting = models.PositiveIntegerField(default=0)
    ed_lwbs = models.PositiveIntegerField(default=0, help_text="Left without being seen")
    or_cases_scheduled = models.PositiveIntegerField(default=0)
    or_cases_in_progress = models.PositiveIntegerField(default=0)
    pending_admissions = models.PositiveIntegerField(default=0)
    pending_discharges = models.PositiveIntegerField(default=0)
    pending_transfers = models.PositiveIntegerField(default=0)
    occupancy_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    icu_occupancy_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    capacity_status = models.CharField(
        max_length=20, choices=CapacityStatus.choices, default=CapacityStatus.NORMAL
    )
    rn_on_duty = models.PositiveIntegerField(default=0)
    md_on_duty = models.PositiveIntegerField(default=0)
    hap_infections_mtd = models.PositiveIntegerField(default=0, help_text="Hospital-acquired infections month-to-date")
    falls_mtd = models.PositiveIntegerField(default=0)
    pressure_injuries_mtd = models.PositiveIntegerField(default=0)
    patient_satisfaction_score = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)

    class Meta:
        db_table = "cymed_hospital_command_center_snapshots"
        ordering = ["-snapshot_time"]
        indexes = [
            models.Index(fields=["tenant_id", "snapshot_time"]),
        ]

    def __str__(self) -> str:
        return f"Snapshot({self.tenant_id}, {self.snapshot_time}, {self.capacity_status})"


class CommandCenterAlert(BaseModel):
    """Real-time operational alert requiring attention."""
    alert_code = models.CharField(max_length=100, db_index=True)
    title = models.CharField(max_length=255)
    title_ar = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    severity = models.CharField(max_length=20, choices=AlertSeverity.choices, default=AlertSeverity.MEDIUM)
    status = models.CharField(max_length=20, choices=AlertStatus.choices, default=AlertStatus.ACTIVE)
    category = models.CharField(max_length=100, blank=True)
    department = models.CharField(max_length=200, blank=True)
    location = models.CharField(max_length=255, blank=True)
    triggered_at = models.DateTimeField(auto_now_add=True, db_index=True)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    acknowledged_by = models.CharField(max_length=255, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.CharField(max_length=255, blank=True)
    resolution_notes = models.TextField(blank=True)
    escalated_at = models.DateTimeField(null=True, blank=True)
    escalated_to = models.CharField(max_length=255, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "cymed_hospital_command_center_alerts"
        ordering = ["-triggered_at"]
        indexes = [
            models.Index(fields=["tenant_id", "status", "severity"]),
            models.Index(fields=["tenant_id", "triggered_at"]),
        ]

    def __str__(self) -> str:
        return f"Alert({self.alert_code}, {self.severity}, {self.status})"


class CapacityThreshold(BaseModel):
    """Configurable capacity thresholds per unit/department."""
    unit_name = models.CharField(max_length=255)
    unit_code = models.CharField(max_length=50, blank=True)
    total_capacity = models.PositiveIntegerField()
    elevated_threshold_pct = models.DecimalField(max_digits=5, decimal_places=2, default=75)
    high_threshold_pct = models.DecimalField(max_digits=5, decimal_places=2, default=85)
    critical_threshold_pct = models.DecimalField(max_digits=5, decimal_places=2, default=95)
    auto_alert_enabled = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "cymed_hospital_capacity_thresholds"
        unique_together = [("tenant_id", "unit_code")]

    def __str__(self) -> str:
        return f"Threshold({self.unit_name}, cap={self.total_capacity})"


class HospitalDiversionStatus(BaseModel):
    """Tracks hospital-level diversion events (ED, ambulance, specialty)."""

    class DiversionType(models.TextChoices):
        AMBULANCE = "ambulance", "Ambulance Diversion"
        ED = "ed", "ED Diversion"
        SPECIALTY = "specialty", "Specialty Diversion"
        FULL = "full", "Full Diversion"

    diversion_type = models.CharField(max_length=30, choices=DiversionType.choices)
    started_at = models.DateTimeField()
    ended_at = models.DateTimeField(null=True, blank=True)
    reason = models.TextField()
    approved_by = models.CharField(max_length=255)
    notified_agencies = models.JSONField(default=list, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = "cymed_hospital_diversion_status"
        ordering = ["-started_at"]

    def __str__(self) -> str:
        return f"Diversion({self.diversion_type}, active={self.is_active})"


class BedTurnoverLog(BaseModel):
    """Logs bed turnaround times for capacity optimization."""
    bed_id = models.CharField(max_length=255)
    unit_name = models.CharField(max_length=255)
    patient_discharge_time = models.DateTimeField()
    cleaning_start_time = models.DateTimeField(null=True, blank=True)
    cleaning_end_time = models.DateTimeField(null=True, blank=True)
    next_patient_admitted_time = models.DateTimeField(null=True, blank=True)
    turnaround_minutes = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        db_table = "cymed_hospital_bed_turnover_logs"
        ordering = ["-patient_discharge_time"]

    def __str__(self) -> str:
        return f"BedTurnover(bed={self.bed_id}, {self.turnaround_minutes}min)"


class CommandCenterKPI(BaseModel):
    """Persisted KPI metrics for dashboard trend analysis."""
    kpi_date = models.DateField(db_index=True)
    kpi_name = models.CharField(max_length=200, db_index=True)
    kpi_value = models.DecimalField(max_digits=12, decimal_places=4)
    kpi_unit = models.CharField(max_length=50, blank=True)
    target_value = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    department = models.CharField(max_length=200, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "cymed_hospital_command_center_kpis"
        unique_together = [("tenant_id", "kpi_date", "kpi_name", "department")]
        ordering = ["-kpi_date"]

    def __str__(self) -> str:
        return f"KPI({self.kpi_name}={self.kpi_value}, {self.kpi_date})"
