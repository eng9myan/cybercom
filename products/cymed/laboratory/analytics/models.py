"""
CyMed Laboratory — Analytics
Pre-aggregated metrics snapshots for dashboards and reporting.
Raw data streams to CyData for deep analytics — no duplication.
"""
from django.db import models
from platform.common.models import BaseModel


class LabOperationsDashboard(BaseModel):
    """Daily operational snapshot per department — powers lab ops dashboard."""
    snapshot_date = models.DateField()
    department = models.CharField(max_length=50)
    total_orders = models.PositiveIntegerField(default=0)
    orders_completed = models.PositiveIntegerField(default=0)
    orders_pending = models.PositiveIntegerField(default=0)
    orders_cancelled = models.PositiveIntegerField(default=0)
    specimens_received = models.PositiveIntegerField(default=0)
    specimens_rejected = models.PositiveIntegerField(default=0)
    critical_results = models.PositiveIntegerField(default=0)
    critical_results_notified = models.PositiveIntegerField(default=0)
    qc_runs = models.PositiveIntegerField(default=0)
    qc_failures = models.PositiveIntegerField(default=0)
    average_tat_hours = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    stat_average_tat_hours = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    within_tat_target_pct = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    class Meta:
        db_table = "cymed_lab_ops_dashboard"
        unique_together = [("tenant_id", "snapshot_date", "department")]
        indexes = [models.Index(fields=["tenant_id", "snapshot_date"])]


class LabTurnaroundMetric(BaseModel):
    """Per-test TAT tracking — measures time from collection to result approval."""
    PERIOD_TYPES = [("daily", "Daily"), ("weekly", "Weekly"), ("monthly", "Monthly")]

    department = models.CharField(max_length=50)
    test_code = models.CharField(max_length=100, blank=True)
    test_name = models.CharField(max_length=255, blank=True)
    period_type = models.CharField(max_length=10, choices=PERIOD_TYPES, default="daily")
    period_start = models.DateField()
    period_end = models.DateField()
    target_tat_hours = models.DecimalField(max_digits=6, decimal_places=2)
    actual_tat_mean_hours = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    actual_tat_median_hours = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    actual_tat_p95_hours = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    within_target_pct = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    sample_count = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "cymed_lab_tat_metrics"
        indexes = [models.Index(fields=["tenant_id", "department", "period_start"])]


class LabProductivityReport(BaseModel):
    """Technologist productivity metrics per shift/period."""
    PERIOD_TYPES = [("daily", "Daily"), ("weekly", "Weekly"), ("monthly", "Monthly")]

    technologist_id = models.UUIDField()
    period_type = models.CharField(max_length=10, choices=PERIOD_TYPES, default="daily")
    period_start = models.DateField()
    period_end = models.DateField()
    tests_completed = models.PositiveIntegerField(default=0)
    tests_verified = models.PositiveIntegerField(default=0)
    tests_approved = models.PositiveIntegerField(default=0)
    critical_results_handled = models.PositiveIntegerField(default=0)
    qc_runs_performed = models.PositiveIntegerField(default=0)
    specimens_accessioned = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "cymed_lab_productivity_reports"
        unique_together = [("tenant_id", "technologist_id", "period_type", "period_start")]


class LabQualityDashboard(BaseModel):
    """Monthly quality metrics snapshot for quality officer review."""
    period_month = models.PositiveSmallIntegerField()
    period_year = models.PositiveSmallIntegerField()
    department = models.CharField(max_length=50)
    qc_pass_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    rejection_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    repeat_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    critical_notification_compliance_pct = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    proficiency_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    open_failures = models.PositiveIntegerField(default=0)
    total_qc_failures = models.PositiveIntegerField(default=0)
    corrective_actions_open = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "cymed_lab_quality_dashboard"
        unique_together = [("tenant_id", "department", "period_year", "period_month")]


class LabMicrobiologyDashboard(BaseModel):
    """Monthly microbiology metrics for infection control reporting."""
    period_month = models.PositiveSmallIntegerField()
    period_year = models.PositiveSmallIntegerField()
    total_cultures = models.PositiveIntegerField(default=0)
    positive_cultures = models.PositiveIntegerField(default=0)
    contamination_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    mrsa_isolates = models.PositiveIntegerField(default=0)
    esbl_isolates = models.PositiveIntegerField(default=0)
    cre_isolates = models.PositiveIntegerField(default=0)
    mdr_isolates = models.PositiveIntegerField(default=0)
    blood_culture_tat_mean_hours = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)

    class Meta:
        db_table = "cymed_lab_microbiology_dashboard"
        unique_together = [("tenant_id", "period_year", "period_month")]
