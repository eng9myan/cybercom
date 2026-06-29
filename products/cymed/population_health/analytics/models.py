"""
CyMed Population Health — Analytics
Covers: NationalHealthSnapshot, PopulationAnalyticsInsight, QualityKPIDashboard,
        OutbreakForecast, PopulationHealthDashboard
Terminology: ICD-11 codes resolved via TerminologyService (not stored locally).
"""

from django.db import models

from platform.common.models import BaseModel

PERIOD_TYPE_CHOICES = [
    ("daily", "Daily"),
    ("weekly", "Weekly"),
    ("monthly", "Monthly"),
    ("quarterly", "Quarterly"),
    ("annual", "Annual"),
]

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


class NationalHealthSnapshot(BaseModel):
    """Periodic snapshot of aggregated national/regional health metrics."""

    snapshot_date = models.DateField()
    period_type = models.CharField(max_length=10, choices=PERIOD_TYPE_CHOICES)
    geographic_scope = models.CharField(max_length=200, blank=True)
    total_population = models.PositiveIntegerField(default=0)
    registered_patients = models.PositiveIntegerField(default=0)
    disease_prevalence = models.JSONField(default=dict)
    vaccination_coverage = models.JSONField(default=dict)
    care_gap_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    risk_distribution = models.JSONField(default=dict)
    active_outbreaks = models.PositiveIntegerField(default=0)
    program_enrollment_count = models.PositiveIntegerField(default=0)
    quality_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    class Meta:
        db_table = "cymed_ph_ana_health_snapshots"
        unique_together = [["tenant_id", "snapshot_date", "period_type", "geographic_scope"]]

    def __str__(self):
        return f"{self.period_type} snapshot — {self.snapshot_date} [{self.geographic_scope or 'national'}]"


class PopulationAnalyticsInsight(BaseModel):
    """An AI-generated or rule-based insight about population health trends."""

    INSIGHT_TYPE_CHOICES = [
        ("disease_trend", "Disease Trend"),
        ("care_gap", "Care Gap"),
        ("risk_pattern", "Risk Pattern"),
        ("program_effectiveness", "Program Effectiveness"),
        ("outbreak_risk", "Outbreak Risk"),
        ("vaccination_gap", "Vaccination Gap"),
        ("quality_gap", "Quality Gap"),
        ("population_shift", "Population Shift"),
    ]
    SCOPE_TYPE_CHOICES = [
        ("patient", "Patient"),
        ("population_group", "Population Group"),
        ("facility", "Facility"),
        ("region", "Region"),
        ("national", "National"),
    ]
    STATUS_CHOICES = [
        ("pending_review", "Pending Review"),
        ("acknowledged", "Acknowledged"),
        ("acted_upon", "Acted Upon"),
        ("dismissed", "Dismissed"),
    ]

    insight_type = models.CharField(max_length=30, choices=INSIGHT_TYPE_CHOICES)
    scope_type = models.CharField(max_length=20, choices=SCOPE_TYPE_CHOICES)
    scope_id = models.UUIDField(null=True, blank=True)
    insight_title = models.CharField(max_length=500)
    insight_detail = models.TextField()
    confidence_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    estimated_impact = models.TextField(blank=True)
    is_ai_generated = models.BooleanField(default=False)
    is_advisory_only = models.BooleanField(default=True, editable=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending_review")
    acknowledged_by_user_id = models.UUIDField(null=True, blank=True)
    acknowledged_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "cymed_ph_ana_insights"

    def __str__(self):
        return f"{self.insight_type} — {self.insight_title[:60]} [{self.status}]"


class QualityKPIDashboard(BaseModel):
    """A single KPI measurement for quality tracking dashboards."""

    KPI_CATEGORY_CHOICES = [
        ("clinical_quality", "Clinical Quality"),
        ("patient_safety", "Patient Safety"),
        ("access", "Access"),
        ("efficiency", "Efficiency"),
        ("patient_experience", "Patient Experience"),
        ("population_health", "Population Health"),
    ]
    TREND_DIRECTION_CHOICES = [
        ("improving", "Improving"),
        ("stable", "Stable"),
        ("declining", "Declining"),
        ("unknown", "Unknown"),
    ]

    kpi_name = models.CharField(max_length=200)
    kpi_category = models.CharField(max_length=30, choices=KPI_CATEGORY_CHOICES)
    facility_id = models.UUIDField(null=True, blank=True)
    period_start = models.DateField()
    period_end = models.DateField()
    current_value = models.DecimalField(max_digits=10, decimal_places=2)
    target_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    unit = models.CharField(max_length=50, blank=True)
    meets_target = models.BooleanField(default=False)
    trend_direction = models.CharField(
        max_length=10, choices=TREND_DIRECTION_CHOICES, default="unknown"
    )

    class Meta:
        db_table = "cymed_ph_ana_quality_kpis"

    def __str__(self):
        return f"{self.kpi_name} [{self.kpi_category}] {self.period_start}–{self.period_end}"


class OutbreakForecast(BaseModel):
    """AI/model-generated forecast of a potential disease outbreak."""

    RISK_LEVEL_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
        ("critical", "Critical"),
    ]

    disease_code = models.CharField(max_length=20)
    disease_name = models.CharField(max_length=200)
    forecast_date = models.DateField()
    forecast_period_days = models.PositiveSmallIntegerField(default=30)
    predicted_cases = models.PositiveIntegerField(null=True, blank=True)
    confidence_interval_low = models.PositiveIntegerField(null=True, blank=True)
    confidence_interval_high = models.PositiveIntegerField(null=True, blank=True)
    risk_level = models.CharField(max_length=10, choices=RISK_LEVEL_CHOICES, default="low")
    geographic_scope = models.CharField(max_length=200, blank=True)
    is_ai_generated = models.BooleanField(default=False)
    is_advisory_only = models.BooleanField(default=True, editable=False)
    model_version = models.CharField(max_length=50, blank=True)

    class Meta:
        db_table = "cymed_ph_ana_outbreak_forecasts"

    def __str__(self):
        return f"{self.disease_name} forecast — {self.forecast_date} [{self.risk_level}]"


class PopulationHealthDashboard(BaseModel):
    """Aggregated population health dashboard view for a facility or region."""

    DASHBOARD_TYPE_CHOICES = [
        ("population_health", "Population Health"),
        ("registry", "Registry"),
        ("public_health", "Public Health"),
        ("national", "National"),
        ("ministry", "Ministry"),
        ("surveillance", "Surveillance"),
    ]

    dashboard_name = models.CharField(max_length=200)
    dashboard_type = models.CharField(max_length=30, choices=DASHBOARD_TYPE_CHOICES)
    facility_id = models.UUIDField(null=True, blank=True)
    geographic_scope = models.CharField(max_length=200, blank=True)
    as_of_date = models.DateField()
    total_enrolled_patients = models.PositiveIntegerField(default=0)
    high_risk_patients = models.PositiveIntegerField(default=0)
    open_care_gaps = models.PositiveIntegerField(default=0)
    active_programs = models.PositiveIntegerField(default=0)
    vaccination_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    disease_registry_count = models.PositiveIntegerField(default=0)
    kpi_summary = models.JSONField(default=dict)

    class Meta:
        db_table = "cymed_ph_ana_dashboards"

    def __str__(self):
        return f"{self.dashboard_name} [{self.dashboard_type}] as of {self.as_of_date}"
