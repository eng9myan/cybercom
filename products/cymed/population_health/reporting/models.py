"""
CyMed Population Health — Reporting
Covers: NationalReport, ReportTemplate, GovernmentSubmission, ReportSchedule
"""

from django.db import models

from platform.common.models import BaseModel

REPORT_TYPE_CHOICES = [
    ("annual_health", "Annual Health"),
    ("disease_surveillance", "Disease Surveillance"),
    ("registry_report", "Registry Report"),
    ("vaccination_coverage", "Vaccination Coverage"),
    ("quality_report", "Quality Report"),
    ("outbreak_report", "Outbreak Report"),
    ("program_report", "Program Report"),
    ("ministry_report", "Ministry Report"),
    ("who_report", "WHO Report"),
]


class NationalReport(BaseModel):
    """A formal national or regional health report submitted to authorities."""

    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("in_review", "In Review"),
        ("approved", "Approved"),
        ("submitted", "Submitted"),
        ("published", "Published"),
    ]

    report_name = models.CharField(max_length=200)
    report_type = models.CharField(max_length=30, choices=REPORT_TYPE_CHOICES)
    reporting_period_start = models.DateField()
    reporting_period_end = models.DateField()
    report_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    generated_by_user_id = models.UUIDField(null=True, blank=True)
    approved_by_user_id = models.UUIDField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    submitted_to_authority = models.CharField(max_length=200, blank=True)
    content = models.JSONField(default=dict)
    fhir_measure_report_id = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        db_table = "cymed_ph_rep_reports"

    def __str__(self):
        return f"{self.report_name} [{self.report_type}] — {self.status}"


class ReportTemplate(BaseModel):
    """A reusable template that defines structure for a given report type."""

    template_name = models.CharField(max_length=200)
    report_type = models.CharField(max_length=30, choices=REPORT_TYPE_CHOICES)
    template_definition = models.JSONField(default=dict)
    is_national_standard = models.BooleanField(default=False)
    governing_standard = models.CharField(max_length=200, blank=True)
    version = models.CharField(max_length=20, default="1.0")
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "cymed_ph_rep_templates"

    def __str__(self):
        return f"{self.template_name} v{self.version} [{self.report_type}]"


class GovernmentSubmission(BaseModel):
    """Records a submission of a NationalReport to a government authority."""

    SUBMISSION_METHOD_CHOICES = [
        ("electronic", "Electronic"),
        ("api", "API"),
        ("email", "Email"),
        ("portal", "Portal"),
        ("manual", "Manual"),
    ]
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("submitted", "Submitted"),
        ("acknowledged", "Acknowledged"),
        ("rejected", "Rejected"),
        ("accepted", "Accepted"),
    ]

    national_report = models.ForeignKey(
        NationalReport,
        on_delete=models.PROTECT,
        related_name="submissions",
    )
    submission_date = models.DateTimeField()
    submitted_by_user_id = models.UUIDField()
    submission_method = models.CharField(
        max_length=20, choices=SUBMISSION_METHOD_CHOICES, default="electronic"
    )
    submission_endpoint = models.CharField(max_length=500, blank=True)
    reference_number = models.CharField(max_length=200, blank=True, null=True)
    acknowledgement_received = models.BooleanField(default=False)
    acknowledgement_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    rejection_reason = models.TextField(blank=True)

    class Meta:
        db_table = "cymed_ph_rep_submissions"

    def __str__(self):
        return (
            f"Submission of '{self.national_report}' via {self.submission_method} [{self.status}]"
        )


class ReportSchedule(BaseModel):
    """Defines the schedule and automation settings for recurring reports."""

    FREQUENCY_CHOICES = [
        ("weekly", "Weekly"),
        ("monthly", "Monthly"),
        ("quarterly", "Quarterly"),
        ("annual", "Annual"),
        ("as_needed", "As Needed"),
    ]

    report_type = models.CharField(max_length=30, choices=REPORT_TYPE_CHOICES)
    schedule_name = models.CharField(max_length=200)
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    next_due_date = models.DateField()
    responsible_user_id = models.UUIDField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    last_generated_at = models.DateTimeField(null=True, blank=True)
    auto_generate = models.BooleanField(default=False)
    auto_submit = models.BooleanField(default=False)
    submission_authority = models.CharField(max_length=200, blank=True)

    class Meta:
        db_table = "cymed_ph_rep_schedules"

    def __str__(self):
        return f"{self.schedule_name} [{self.report_type}] — {self.frequency}"
