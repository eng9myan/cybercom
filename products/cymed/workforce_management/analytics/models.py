from django.db import models
from platform.common.models import BaseModel


REPORT_TYPE_CHOICES = [
    ("staffing_coverage", "Staffing Coverage Report"),
    ("fatigue_compliance", "Fatigue & Duty Hour Compliance"),
    ("credential_expiry", "Credential Expiry Report"),
    ("overtime_analysis", "Overtime Analysis"),
    ("agency_utilization", "Agency Staff Utilization"),
    ("float_pool_usage", "Float Pool Usage"),
    ("acuity_trend", "Patient Acuity Trend"),
    ("oncall_response", "On-Call Response SLA Report"),
    ("roster_compliance", "Roster Compliance Audit"),
    ("vacancy_rate", "Shift Vacancy Rate"),
]

SNAPSHOT_PERIOD_CHOICES = [
    ("daily", "Daily"),
    ("weekly", "Weekly"),
    ("monthly", "Monthly"),
    ("quarterly", "Quarterly"),
]


class WorkforceAnalyticsSnapshot(BaseModel):
    class Meta:
        app_label = "cymed_hwm_analytics"
        db_table = "cymed_hwm_analytics_snapshot"
        unique_together = [["tenant_id", "facility_id", "department_id", "period_start", "period_type"]]

    facility_id = models.UUIDField(db_index=True)
    department_id = models.UUIDField(db_index=True, null=True, blank=True)
    period_type = models.CharField(max_length=15, choices=SNAPSHOT_PERIOD_CHOICES, default="monthly")
    period_start = models.DateField(db_index=True)
    period_end = models.DateField()

    total_fte = models.DecimalField(max_digits=7, decimal_places=2, default=0)
    avg_nurse_patient_ratio = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    coverage_compliance_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    overtime_hours = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    agency_hours = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    float_deployments = models.PositiveIntegerField(default=0)
    vacancy_shifts = models.PositiveIntegerField(default=0)
    total_shifts = models.PositiveIntegerField(default=0)
    vacancy_rate_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    fatigue_violations = models.PositiveIntegerField(default=0)
    shortage_alerts = models.PositiveIntegerField(default=0)
    avg_oncall_response_min = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"Analytics {self.facility_id} {self.period_start} ({self.period_type})"


class WorkforceReport(BaseModel):
    class Meta:
        app_label = "cymed_hwm_analytics"
        db_table = "cymed_hwm_analytics_report"

    generated_by_id = models.UUIDField(db_index=True)
    report_type = models.CharField(max_length=40, choices=REPORT_TYPE_CHOICES)
    facility_id = models.UUIDField(db_index=True)
    department_id = models.UUIDField(db_index=True, null=True, blank=True)
    period_start = models.DateField()
    period_end = models.DateField()
    report_data = models.JSONField(default=dict)
    generated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Report {self.report_type} {self.period_start} — {self.period_end}"


class OnCallSLAMetric(BaseModel):
    class Meta:
        app_label = "cymed_hwm_analytics"
        db_table = "cymed_hwm_analytics_oncall_sla"

    facility_id = models.UUIDField(db_index=True)
    specialty = models.CharField(max_length=100)
    metric_date = models.DateField(db_index=True)
    total_pages = models.PositiveIntegerField(default=0)
    pages_within_sla = models.PositiveIntegerField(default=0)
    pages_escalated = models.PositiveIntegerField(default=0)
    avg_response_minutes = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    sla_compliance_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    def __str__(self):
        return f"SLA Metric {self.specialty} {self.metric_date}"
