from django.db import models

from platform.common.models import BaseModel

VIOLATION_TYPE_CHOICES = [
    ("max_weekly_hours", "Maximum Weekly Hours Exceeded"),
    ("max_consecutive_days", "Maximum Consecutive Days Exceeded"),
    ("min_rest_period", "Minimum Rest Period Violated"),
    ("max_shift_length", "Maximum Shift Length Exceeded"),
    ("consecutive_night_cap", "Consecutive Night Shifts Cap Exceeded"),
    ("acgme_80h_weekly", "ACGME 80-Hour Weekly Cap"),
    ("acgme_max_shift_28h", "ACGME 28-Hour Shift Limit"),
    ("acgme_rest_14h", "ACGME 14-Hour Rest After 24h Shift"),
    ("acgme_call_frequency", "ACGME 1-in-3 Call Frequency"),
    ("duty_hour_warning", "Duty Hour Warning (75+ hours in 7 days)"),
]

VIOLATION_STATUS_CHOICES = [
    ("active", "Active"),
    ("overridden", "Override Approved"),
    ("resolved", "Resolved"),
]


class DutyHourLog(BaseModel):
    class Meta:
        app_label = "cymed_hwm_fatigue"
        db_table = "cymed_hwm_fatigue_duty_log"

    workforce_profile_id = models.UUIDField(db_index=True)
    roster_slot_id = models.UUIDField(db_index=True, null=True, blank=True)
    clock_in = models.DateTimeField()
    clock_out = models.DateTimeField(null=True, blank=True)
    hours_worked = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    is_resident = models.BooleanField(default=False)
    is_night_shift = models.BooleanField(default=False)
    is_weekend = models.BooleanField(default=False)
    # Includes handover time beyond nominal shift
    includes_handover = models.BooleanField(default=False)
    facility_id = models.UUIDField(db_index=True)

    def __str__(self):
        return f"Duty log {self.workforce_profile_id} {self.clock_in}"


class WeeklyHoursSummary(BaseModel):
    class Meta:
        app_label = "cymed_hwm_fatigue"
        db_table = "cymed_hwm_fatigue_weekly_summary"
        unique_together = [["tenant_id", "workforce_profile_id", "week_start"]]

    workforce_profile_id = models.UUIDField(db_index=True)
    week_start = models.DateField(db_index=True)
    total_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    night_shift_count = models.PositiveSmallIntegerField(default=0)
    consecutive_days_worked = models.PositiveSmallIntegerField(default=0)
    is_resident = models.BooleanField(default=False)
    # ACGME: rolling 4-week average for residents
    rolling_4wk_avg_hours = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )

    def __str__(self):
        return f"Weekly summary {self.workforce_profile_id} w/o {self.week_start}"


class FatigueViolation(BaseModel):
    class Meta:
        app_label = "cymed_hwm_fatigue"
        db_table = "cymed_hwm_fatigue_violation"

    workforce_profile_id = models.UUIDField(db_index=True)
    roster_slot_id = models.UUIDField(db_index=True, null=True, blank=True)
    violation_type = models.CharField(max_length=50, choices=VIOLATION_TYPE_CHOICES)
    detected_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=VIOLATION_STATUS_CHOICES, default="active")
    override_by_id = models.UUIDField(null=True, blank=True)
    override_reason = models.TextField(blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    # For ACGME 28h: revoking prescribing authority flag
    prescribing_authority_revoked = models.BooleanField(default=False)

    def __str__(self):
        return f"Fatigue violation {self.violation_type} — {self.workforce_profile_id}"


class DisasterOverride(BaseModel):
    class Meta:
        app_label = "cymed_hwm_fatigue"
        db_table = "cymed_hwm_fatigue_disaster_override"

    # Activated by Medical Director or Director of Nursing
    authorized_by_id = models.UUIDField(db_index=True)
    authorized_by_role = models.CharField(max_length=100)
    incident_id = models.CharField(max_length=200, db_index=True)
    facility_id = models.UUIDField(db_index=True)
    activated_at = models.DateTimeField(auto_now_add=True)
    deactivated_at = models.DateTimeField(null=True, blank=True)
    override_reason = models.TextField()
    # All fatigue violations during this override are auto-flagged for post-incident review
    affected_violations = models.JSONField(default=list)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Disaster Override — incident {self.incident_id} ({'active' if self.is_active else 'inactive'})"
