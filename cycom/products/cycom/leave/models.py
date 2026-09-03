from datetime import timedelta

from django.db import models

from platform.common.models import BaseModel
from products.cycom.hr.models import Employee


class LeaveType(BaseModel):
    """A category of leave with its annual allocation (e.g. Annual 14, Sick 14)."""

    name = models.CharField(max_length=100)
    code = models.CharField(max_length=30)
    is_paid = models.BooleanField(default=True)
    days_per_year = models.DecimalField(max_digits=6, decimal_places=1, default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "cycom_leave_types"
        unique_together = [("tenant_id", "code")]
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.days_per_year}d)"


class LeaveRequest(BaseModel):
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("submitted", "Submitted"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
        ("cancelled", "Cancelled"),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="leave_requests")
    leave_type = models.ForeignKey(LeaveType, on_delete=models.PROTECT, related_name="requests")
    start_date = models.DateField()
    end_date = models.DateField()
    days = models.DecimalField(max_digits=6, decimal_places=1, default=0)
    reason = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    approved_by = models.CharField(max_length=255, blank=True)
    rejection_reason = models.TextField(blank=True)

    class Meta:
        db_table = "cycom_leave_requests"
        ordering = ["-start_date"]

    def __str__(self):
        return f"{self.employee} {self.leave_type.code} {self.start_date}→{self.end_date} ({self.status})"

    def compute_days(self):
        """Inclusive calendar days (simplification; working-day calendars later)."""
        if self.end_date < self.start_date:
            return 0
        return (self.end_date - self.start_date).days + 1
