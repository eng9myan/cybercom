"""
Staff attendance: daily check-in/out, lateness, and timesheets.

This is the source of truth for *hours actually worked* and *unpaid leave*, both
of which payroll consumes (see payroll.services.hours_for_period). Student
attendance lives in cyed_attendance and is deliberately separate.
"""

from datetime import datetime, timedelta
from decimal import Decimal

from django.db import models

from platform.common.models import BaseModel

# A standard full day for a full-time staff member, used when a day is marked
# present but no explicit check-in/out times were captured (e.g. bulk import).
STANDARD_DAY_HOURS = Decimal("7.6")  # AU full-time: 38h week / 5
LATE_GRACE_MINUTES = 5


class StaffAttendanceDay(BaseModel):
    STATUS = [
        ("present", "Present"),
        ("late", "Late"),
        ("absent", "Absent (unexplained)"),
        ("sick", "Sick Leave"),
        ("leave", "Approved Leave"),
        ("holiday", "Public Holiday"),
        ("weekend", "Non-working Day"),
    ]
    # Statuses that are paid even though no hours were physically worked.
    PAID_NON_WORKING = {"sick", "leave", "holiday"}
    # Statuses that dock pay.
    UNPAID = {"absent"}

    staff = models.ForeignKey("cyed_hr.Staff", on_delete=models.CASCADE, related_name="attendance_days")
    date = models.DateField()
    scheduled_start = models.TimeField(null=True, blank=True)
    scheduled_end = models.TimeField(null=True, blank=True)
    check_in = models.TimeField(null=True, blank=True)
    check_out = models.TimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default="present")
    minutes_late = models.PositiveIntegerField(default=0)
    hours_worked = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    leave_request = models.ForeignKey(
        "cyed_hr.StaffLeave", on_delete=models.SET_NULL, null=True, blank=True, related_name="attendance_days"
    )
    note = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "cyed_staff_attendance_days"
        ordering = ["-date", "staff__last_name"]
        constraints = [
            models.UniqueConstraint(fields=["tenant_id", "staff", "date"], name="uniq_staff_attendance_per_day")
        ]
        indexes = [models.Index(fields=["tenant_id", "date"], name="idx_staff_att_tenant_date")]

    # ── derived values ────────────────────────────────────────────────────────
    def recompute(self):
        """Derive minutes_late and hours_worked from the captured times."""
        self.minutes_late = 0
        if self.check_in and self.scheduled_start:
            late = (
                datetime.combine(self.date, self.check_in)
                - datetime.combine(self.date, self.scheduled_start)
            ).total_seconds() / 60
            if late > LATE_GRACE_MINUTES:
                self.minutes_late = int(late)
                if self.status == "present":
                    self.status = "late"

        if self.check_in and self.check_out:
            delta = datetime.combine(self.date, self.check_out) - datetime.combine(self.date, self.check_in)
            if delta < timedelta(0):  # overnight shift
                delta += timedelta(days=1)
            self.hours_worked = round(Decimal(delta.total_seconds()) / Decimal(3600), 2)
        elif self.status in ("present", "late"):
            self.hours_worked = STANDARD_DAY_HOURS
        elif self.status in self.PAID_NON_WORKING:
            self.hours_worked = STANDARD_DAY_HOURS
        else:
            self.hours_worked = Decimal("0")

    def save(self, *args, **kwargs):
        self.recompute()
        super().save(*args, **kwargs)

    @property
    def is_paid(self) -> bool:
        return self.status not in self.UNPAID and self.status != "weekend"

    def __str__(self):
        return f"{self.staff_id} {self.date} {self.status}"


class Timesheet(BaseModel):
    """A period roll-up, submitted by staff and approved by a manager."""

    STATUS = [("draft", "Draft"), ("submitted", "Submitted"), ("approved", "Approved"), ("rejected", "Rejected")]

    staff = models.ForeignKey("cyed_hr.Staff", on_delete=models.CASCADE, related_name="timesheets")
    period_label = models.CharField(max_length=50)  # e.g. "2026-02"
    period_start = models.DateField()
    period_end = models.DateField()
    total_hours = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    days_present = models.PositiveSmallIntegerField(default=0)
    days_absent = models.PositiveSmallIntegerField(default=0)
    days_leave = models.PositiveSmallIntegerField(default=0)
    total_minutes_late = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS, default="draft")
    approved_by = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "cyed_staff_timesheets"
        ordering = ["-period_start"]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant_id", "staff", "period_label"], name="uniq_timesheet_per_staff_period"
            )
        ]

    def recalculate(self):
        days = StaffAttendanceDay.objects.filter(
            tenant_id=self.tenant_id, staff=self.staff,
            date__gte=self.period_start, date__lte=self.period_end,
        )
        self.total_hours = sum((d.hours_worked for d in days), Decimal("0"))
        self.days_present = days.filter(status__in=["present", "late"]).count()
        self.days_absent = days.filter(status="absent").count()
        self.days_leave = days.filter(status__in=["leave", "sick"]).count()
        self.total_minutes_late = sum((d.minutes_late for d in days), 0)
        self.save()
        return self

    def __str__(self):
        return f"Timesheet {self.staff_id} {self.period_label} ({self.status})"
