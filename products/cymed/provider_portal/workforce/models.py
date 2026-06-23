from django.db import models
from platform.common.models import BaseModel


class ProviderSchedule(BaseModel):
    SHIFT_TYPE_CHOICES = [
        ("morning", "Morning"),
        ("afternoon", "Afternoon"),
        ("evening", "Evening"),
        ("night", "Night"),
        ("on_call", "On Call"),
        ("administrative", "Administrative"),
    ]
    STATUS_CHOICES = [
        ("scheduled", "Scheduled"),
        ("confirmed", "Confirmed"),
        ("swapped", "Swapped"),
        ("cancelled", "Cancelled"),
        ("completed", "Completed"),
    ]

    provider_id = models.UUIDField(db_index=True)
    provider_type = models.CharField(max_length=100)
    provider_name = models.CharField(max_length=255)
    unit_id = models.UUIDField(null=True, blank=True)
    unit_name = models.CharField(max_length=255, blank=True)
    department = models.CharField(max_length=255, blank=True)
    schedule_date = models.DateField(db_index=True)
    shift_type = models.CharField(max_length=30, choices=SHIFT_TYPE_CHOICES, default="morning")
    shift_start = models.TimeField()
    shift_end = models.TimeField()
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default="scheduled")
    cycom_schedule_id = models.UUIDField(null=True, blank=True)
    location = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "cymed_prov_schedules"
        indexes = [
            models.Index(fields=["tenant_id", "provider_id", "schedule_date"]),
            models.Index(fields=["tenant_id", "unit_id", "schedule_date"]),
        ]

    def __str__(self):
        return f"{self.provider_name} — {self.schedule_date} ({self.shift_type})"


class ShiftAssignment(BaseModel):
    ASSIGNMENT_TYPE_CHOICES = [
        ("regular", "Regular"),
        ("swap", "Swap"),
        ("coverage", "Coverage"),
        ("float", "Float"),
    ]

    schedule = models.ForeignKey(
        ProviderSchedule,
        on_delete=models.CASCADE,
        related_name="assignments",
    )
    original_provider_id = models.UUIDField()
    covering_provider_id = models.UUIDField()
    assignment_type = models.CharField(max_length=30, choices=ASSIGNMENT_TYPE_CHOICES, default="regular")
    approved_by = models.UUIDField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    is_approved = models.BooleanField(default=False)
    reason = models.TextField(blank=True)

    class Meta:
        db_table = "cymed_prov_shift_assignments"

    def __str__(self):
        return f"Assignment {self.assignment_type} — schedule {self.schedule_id}"


class LeaveRequest(BaseModel):
    LEAVE_TYPE_CHOICES = [
        ("annual", "Annual"),
        ("sick", "Sick"),
        ("emergency", "Emergency"),
        ("unpaid", "Unpaid"),
        ("maternity", "Maternity"),
        ("paternity", "Paternity"),
        ("study", "Study"),
        ("conference", "Conference"),
        ("sabbatical", "Sabbatical"),
    ]
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
        ("cancelled", "Cancelled"),
    ]

    provider_id = models.UUIDField(db_index=True)
    provider_name = models.CharField(max_length=255)
    leave_type = models.CharField(max_length=30, choices=LEAVE_TYPE_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField()
    total_days = models.PositiveSmallIntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    reason = models.TextField(blank=True)
    approved_by = models.UUIDField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    cycom_leave_id = models.UUIDField(null=True, blank=True)

    class Meta:
        db_table = "cymed_prov_leave_requests"

    def __str__(self):
        return f"{self.provider_name} — {self.leave_type} ({self.start_date} to {self.end_date})"


class AttendanceRecord(BaseModel):
    STATUS_CHOICES = [
        ("present", "Present"),
        ("absent", "Absent"),
        ("late", "Late"),
        ("early_leave", "Early Leave"),
        ("on_leave", "On Leave"),
        ("off_day", "Off Day"),
    ]

    provider_id = models.UUIDField(db_index=True)
    provider_name = models.CharField(max_length=255)
    attendance_date = models.DateField(db_index=True)
    check_in_time = models.TimeField(null=True, blank=True)
    check_out_time = models.TimeField(null=True, blank=True)
    actual_hours = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="present")
    cycom_attendance_id = models.UUIDField(null=True, blank=True)

    class Meta:
        db_table = "cymed_prov_attendance"
        unique_together = [("tenant_id", "provider_id", "attendance_date")]

    def __str__(self):
        return f"{self.provider_name} — {self.attendance_date} ({self.status})"


class CredentialExpiry(BaseModel):
    CREDENTIAL_TYPE_CHOICES = [
        ("medical_license", "Medical License"),
        ("board_certification", "Board Certification"),
        ("bls", "BLS"),
        ("acls", "ACLS"),
        ("pals", "PALS"),
        ("atls", "ATLS"),
        ("specialty_certification", "Specialty Certification"),
        ("dea_registration", "DEA Registration"),
        ("malpractice_insurance", "Malpractice Insurance"),
        ("npi_registration", "NPI Registration"),
        ("other", "Other"),
    ]
    ALERT_STATUS_CHOICES = [
        ("valid", "Valid"),
        ("expiring_soon", "Expiring Soon"),
        ("expired", "Expired"),
    ]

    provider_id = models.UUIDField(db_index=True)
    provider_name = models.CharField(max_length=255)
    credential_type = models.CharField(max_length=50, choices=CREDENTIAL_TYPE_CHOICES)
    credential_name = models.CharField(max_length=255)
    credential_number = models.CharField(max_length=100, blank=True)
    issuing_authority = models.CharField(max_length=255, blank=True)
    issued_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(db_index=True)
    days_until_expiry = models.SmallIntegerField(null=True, blank=True)
    alert_status = models.CharField(max_length=20, choices=ALERT_STATUS_CHOICES, default="valid")
    is_acknowledged = models.BooleanField(default=False)

    class Meta:
        db_table = "cymed_prov_credential_expiry"
        indexes = [
            models.Index(fields=["tenant_id", "provider_id", "expiry_date"]),
            models.Index(fields=["tenant_id", "alert_status"]),
        ]

    def __str__(self):
        return f"{self.provider_name} — {self.credential_name} (expires {self.expiry_date})"
