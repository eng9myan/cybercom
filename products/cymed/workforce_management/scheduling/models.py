from django.db import models
from platform.common.models import BaseModel


SHIFT_TYPE_CHOICES = [
    ("8h_morning", "8-Hour Morning (07:00-15:00)"),
    ("8h_afternoon", "8-Hour Afternoon (15:00-23:00)"),
    ("8h_night", "8-Hour Night (23:00-07:00)"),
    ("12h_day", "12-Hour Day (07:00-19:00)"),
    ("12h_night", "12-Hour Night (19:00-07:00)"),
    ("fixed", "Fixed"),
    ("rotating", "Rotating"),
    ("on_call", "On-Call"),
    ("research_block", "Non-Clinical Research Block"),
]

ROSTER_STATUS_CHOICES = [
    ("draft", "Draft"),
    ("pending_approval", "Pending Approval"),
    ("published", "Published"),
    ("closed", "Closed"),
    ("archived", "Archived"),
]

SLOT_STATUS_CHOICES = [
    ("scheduled", "Scheduled"),
    ("confirmed", "Confirmed"),
    ("checked_in", "Checked In"),
    ("completed", "Completed"),
    ("cancelled", "Cancelled"),
    ("swapped", "Swapped"),
    ("absent", "Absent"),
]


class ShiftTemplate(BaseModel):
    class Meta:
        app_label = "cymed_hwm_scheduling"
        db_table = "cymed_hwm_sched_shift_template"

    name = models.CharField(max_length=200)
    shift_type = models.CharField(max_length=30, choices=SHIFT_TYPE_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    # Shift crosses midnight
    crosses_midnight = models.BooleanField(default=False)
    duration_hours = models.DecimalField(max_digits=4, decimal_places=1)
    # Unpaid break minutes (e.g., 30 for 12h shifts)
    break_minutes = models.PositiveSmallIntegerField(default=0)
    handover_minutes = models.PositiveSmallIntegerField(default=30)
    is_active = models.BooleanField(default=True)
    applicable_department_types = models.JSONField(default=list)

    def __str__(self):
        return f"{self.name} ({self.shift_type})"


class RosterCycle(BaseModel):
    class Meta:
        app_label = "cymed_hwm_scheduling"
        db_table = "cymed_hwm_sched_roster_cycle"

    facility_id = models.UUIDField(db_index=True)
    department_id = models.UUIDField(db_index=True)
    period_start = models.DateField()
    period_end = models.DateField()
    status = models.CharField(max_length=20, choices=ROSTER_STATUS_CHOICES, default="draft")
    published_by_id = models.UUIDField(null=True, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"Roster {self.period_start} to {self.period_end} ({self.status})"


class RosterSlot(BaseModel):
    class Meta:
        app_label = "cymed_hwm_scheduling"
        db_table = "cymed_hwm_sched_roster_slot"

    roster_cycle = models.ForeignKey(
        RosterCycle,
        on_delete=models.CASCADE,
        related_name="slots",
    )
    # FK by ID to workforce_profiles — no cross-app model FK
    workforce_profile_id = models.UUIDField(db_index=True)
    shift_template = models.ForeignKey(
        ShiftTemplate,
        on_delete=models.PROTECT,
        related_name="slots",
    )
    slot_date = models.DateField()
    status = models.CharField(max_length=20, choices=SLOT_STATUS_CHOICES, default="scheduled")
    is_weekend = models.BooleanField(default=False)
    is_holiday = models.BooleanField(default=False)
    is_self_scheduled = models.BooleanField(default=False)
    checked_in_at = models.DateTimeField(null=True, blank=True)
    checked_out_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Slot {self.slot_date} ({self.status})"


class SelfScheduleWindow(BaseModel):
    class Meta:
        app_label = "cymed_hwm_scheduling"
        db_table = "cymed_hwm_sched_self_schedule_window"

    roster_cycle = models.OneToOneField(
        RosterCycle,
        on_delete=models.CASCADE,
        related_name="self_schedule_window",
    )
    opens_at = models.DateTimeField()
    closes_at = models.DateTimeField()
    min_weekend_shifts = models.PositiveSmallIntegerField(default=2)
    min_night_shifts = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Self-schedule window for {self.roster_cycle_id}"


class SlotQuota(BaseModel):
    class Meta:
        app_label = "cymed_hwm_scheduling"
        db_table = "cymed_hwm_sched_slot_quota"

    roster_cycle = models.ForeignKey(
        RosterCycle,
        on_delete=models.CASCADE,
        related_name="slot_quotas",
    )
    shift_template = models.ForeignKey(
        ShiftTemplate,
        on_delete=models.PROTECT,
        related_name="slot_quotas",
    )
    slot_date = models.DateField()
    required_count = models.PositiveSmallIntegerField(default=1)
    filled_count = models.PositiveSmallIntegerField(default=0)
    is_locked = models.BooleanField(default=False)

    def __str__(self):
        return f"Quota {self.slot_date} — {self.shift_template} ({self.filled_count}/{self.required_count})"
