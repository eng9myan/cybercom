import uuid
from django.db import models
from platform.common.models import BaseModel


class ProviderProductivitySnapshot(BaseModel):
    PERIOD_CHOICES = [
        ("daily", "Daily"),
        ("weekly", "Weekly"),
        ("monthly", "Monthly"),
    ]

    provider_id = models.UUIDField(db_index=True)
    provider_name = models.CharField(max_length=255)
    provider_type = models.CharField(max_length=100)
    snapshot_date = models.DateField(db_index=True)
    snapshot_period = models.CharField(
        max_length=20, choices=PERIOD_CHOICES, default="daily"
    )
    patients_seen = models.PositiveIntegerField(default=0)
    notes_completed = models.PositiveIntegerField(default=0)
    notes_pending = models.PositiveIntegerField(default=0)
    orders_placed = models.PositiveIntegerField(default=0)
    results_reviewed = models.PositiveIntegerField(default=0)
    tasks_completed = models.PositiveIntegerField(default=0)
    tasks_pending = models.PositiveIntegerField(default=0)
    messages_sent = models.PositiveIntegerField(default=0)
    telemedicine_sessions = models.PositiveIntegerField(default=0)
    avg_documentation_time_minutes = models.DecimalField(
        max_digits=6, decimal_places=1, null=True, blank=True
    )
    avg_result_review_minutes = models.DecimalField(
        max_digits=6, decimal_places=1, null=True, blank=True
    )

    class Meta:
        app_label = "cymed_provider_analytics"
        db_table = "cymed_prov_productivity_snapshots"
        indexes = [
            models.Index(
                fields=["tenant_id", "provider_id", "snapshot_date"],
                name="cymed_prov_prod_snap_idx",
            ),
        ]
        unique_together = [
            ("tenant_id", "provider_id", "snapshot_date", "snapshot_period")
        ]

    def __str__(self):
        return (
            f"{self.provider_name} — {self.snapshot_date} ({self.snapshot_period})"
        )


class ClinicalQualityMetric(BaseModel):
    METRIC_TYPE_CHOICES = [
        ("documentation_completion", "Documentation Completion"),
        ("result_acknowledgement", "Result Acknowledgement"),
        ("medication_error_rate", "Medication Error Rate"),
        ("hand_hygiene_compliance", "Hand Hygiene Compliance"),
        ("patient_satisfaction", "Patient Satisfaction"),
        ("readmission_rate", "Readmission Rate"),
        ("mortality_rate", "Mortality Rate"),
        ("infection_rate", "Infection Rate"),
        ("order_accuracy", "Order Accuracy"),
        ("care_gap_closure", "Care Gap Closure"),
    ]
    SCOPE_TYPE_CHOICES = [
        ("provider", "Provider"),
        ("unit", "Unit"),
        ("department", "Department"),
        ("facility", "Facility"),
    ]

    metric_type = models.CharField(max_length=50, choices=METRIC_TYPE_CHOICES)
    metric_name = models.CharField(max_length=255)
    measured_at = models.DateField(db_index=True)
    scope_type = models.CharField(max_length=20, choices=SCOPE_TYPE_CHOICES)
    scope_id = models.UUIDField(db_index=True)
    scope_name = models.CharField(max_length=255)
    numerator = models.DecimalField(max_digits=10, decimal_places=2)
    denominator = models.DecimalField(max_digits=10, decimal_places=2)
    rate = models.DecimalField(
        max_digits=6, decimal_places=2, null=True, blank=True
    )
    target_rate = models.DecimalField(
        max_digits=6, decimal_places=2, null=True, blank=True
    )
    benchmark_rate = models.DecimalField(
        max_digits=6, decimal_places=2, null=True, blank=True
    )
    meets_target = models.BooleanField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        app_label = "cymed_provider_analytics"
        db_table = "cymed_prov_quality_metrics"
        indexes = [
            models.Index(
                fields=["tenant_id", "scope_id", "metric_type", "measured_at"],
                name="cymed_prov_qual_metric_idx",
            ),
        ]

    def __str__(self):
        return f"{self.metric_name} — {self.scope_name} ({self.measured_at})"


class WorkforceDashboardSnapshot(BaseModel):
    unit_id = models.UUIDField(db_index=True, null=True, blank=True)
    unit_name = models.CharField(max_length=255, blank=True)
    department = models.CharField(max_length=255, blank=True)
    snapshot_date = models.DateField(db_index=True)
    total_providers = models.PositiveIntegerField(default=0)
    providers_on_duty = models.PositiveIntegerField(default=0)
    providers_on_leave = models.PositiveIntegerField(default=0)
    providers_on_call = models.PositiveIntegerField(default=0)
    unfilled_shifts = models.PositiveIntegerField(default=0)
    credential_expiry_alerts = models.PositiveIntegerField(default=0)
    pending_leave_requests = models.PositiveIntegerField(default=0)
    open_tasks = models.PositiveIntegerField(default=0)
    critical_alerts_pending = models.PositiveIntegerField(default=0)
    patient_census = models.PositiveIntegerField(default=0)
    staff_patient_ratio = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )

    class Meta:
        app_label = "cymed_provider_analytics"
        db_table = "cymed_prov_workforce_snapshots"
        unique_together = [("tenant_id", "unit_id", "snapshot_date")]

    def __str__(self):
        return f"{self.unit_name or 'Facility'} — {self.snapshot_date}"


class ProviderAIInsight(BaseModel):
    INSIGHT_TYPE_CHOICES = [
        ("care_gap", "Care Gap"),
        ("risk_stratification", "Risk Stratification"),
        ("documentation_suggestion", "Documentation Suggestion"),
        ("coding_suggestion", "Coding Suggestion"),
        ("order_suggestion", "Order Suggestion"),
        ("clinical_alert", "Clinical Alert"),
        ("care_coordination", "Care Coordination"),
    ]
    STATUS_CHOICES = [
        ("pending_review", "Pending Review"),
        ("acknowledged", "Acknowledged"),
        ("acted_upon", "Acted Upon"),
        ("dismissed", "Dismissed"),
    ]

    provider_id = models.UUIDField(db_index=True)
    patient_id = models.UUIDField(db_index=True, null=True, blank=True)
    insight_type = models.CharField(max_length=50, choices=INSIGHT_TYPE_CHOICES)
    insight_title = models.CharField(max_length=255)
    insight_body = models.TextField()
    confidence_score = models.DecimalField(
        max_digits=4, decimal_places=2, null=True, blank=True
    )
    source_data = models.JSONField(default=dict)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="pending_review"
    )
    acknowledged_by = models.UUIDField(null=True, blank=True)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    action_taken = models.TextField(blank=True)
    is_advisory_only = models.BooleanField(default=True, editable=False)

    class Meta:
        app_label = "cymed_provider_analytics"
        db_table = "cymed_prov_ai_insights"
        indexes = [
            models.Index(
                fields=["tenant_id", "provider_id", "insight_type", "status"],
                name="cymed_prov_ai_insight_idx",
            ),
        ]

    def __str__(self):
        return f"{self.insight_title} ({self.insight_type}) — {self.status}"


class ExecutiveDashboardMetric(BaseModel):
    METRIC_CATEGORY_CHOICES = [
        ("clinical_quality", "Clinical Quality"),
        ("workforce", "Workforce"),
        ("financial", "Financial"),
        ("operational", "Operational"),
        ("patient_safety", "Patient Safety"),
        ("research", "Research"),
    ]
    TREND_DIRECTION_CHOICES = [
        ("improving", "Improving"),
        ("stable", "Stable"),
        ("declining", "Declining"),
        ("unknown", "Unknown"),
    ]

    metric_category = models.CharField(max_length=30, choices=METRIC_CATEGORY_CHOICES)
    metric_name = models.CharField(max_length=255)
    metric_value = models.DecimalField(max_digits=15, decimal_places=2)
    metric_unit = models.CharField(max_length=50, blank=True)
    metric_date = models.DateField(db_index=True)
    facility_id = models.UUIDField(null=True, blank=True)
    department = models.CharField(max_length=255, blank=True)
    comparison_value = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    trend_direction = models.CharField(
        max_length=20, choices=TREND_DIRECTION_CHOICES, default="unknown"
    )
    alert_threshold = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    is_above_threshold = models.BooleanField(null=True, blank=True)

    class Meta:
        app_label = "cymed_provider_analytics"
        db_table = "cymed_prov_exec_metrics"
        indexes = [
            models.Index(
                fields=["tenant_id", "metric_category", "metric_date"],
                name="cymed_prov_exec_metric_idx",
            ),
        ]

    def __str__(self):
        return f"{self.metric_name} ({self.metric_category}) — {self.metric_date}"
