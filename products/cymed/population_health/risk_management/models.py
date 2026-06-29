"""
CyMed Population Health — Risk Management
Covers: RiskScore, RiskFactor, RiskCategory, RiskAssessment
AI-generated scores are advisory only (is_advisory_only=True, editable=False).
Terminology: ICD-11 codes resolved via TerminologyService.
"""

from django.db import models

from platform.common.models import BaseModel

RISK_CATEGORY_CHOICES = [
    ("readmission", "Readmission"),
    ("mortality", "Mortality"),
    ("chronic_disease", "Chronic Disease"),
    ("high_cost", "High Cost"),
    ("preventable_ed", "Preventable ED"),
    ("falls", "Falls"),
    ("mental_health", "Mental Health"),
    ("sepsis", "Sepsis"),
    ("malnutrition", "Malnutrition"),
]

RISK_LEVEL_CHOICES = [
    ("low", "Low"),
    ("moderate", "Moderate"),
    ("high", "High"),
    ("very_high", "Very High"),
    ("critical", "Critical"),
]


class RiskScore(BaseModel):
    """A computed risk score for a patient within a specific risk category."""

    patient_id = models.UUIDField(db_index=True)
    risk_category = models.CharField(max_length=30, choices=RISK_CATEGORY_CHOICES)
    score = models.DecimalField(max_digits=5, decimal_places=2)
    risk_level = models.CharField(max_length=15, choices=RISK_LEVEL_CHOICES)
    score_date = models.DateField()
    model_version = models.CharField(max_length=50, blank=True)
    is_ai_generated = models.BooleanField(default=False)
    is_advisory_only = models.BooleanField(default=True, editable=False)
    contributing_factors = models.JSONField(default=list)
    valid_until = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "cymed_ph_risk_scores"
        ordering = ["-score_date"]

    def __str__(self):
        return f"{self.risk_category} score {self.score} [{self.risk_level}] — patient {self.patient_id}"


class RiskFactor(BaseModel):
    """An individual factor contributing to a patient risk score."""

    FACTOR_TYPE_CHOICES = [
        ("clinical", "Clinical"),
        ("demographic", "Demographic"),
        ("behavioral", "Behavioral"),
        ("social", "Social"),
        ("historical", "Historical"),
    ]

    risk_score = models.ForeignKey(RiskScore, on_delete=models.CASCADE, related_name="factors")
    factor_name = models.CharField(max_length=200)
    factor_type = models.CharField(max_length=30, choices=FACTOR_TYPE_CHOICES)
    factor_value = models.CharField(max_length=200, blank=True)
    contribution_weight = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    icd11_code = models.CharField(max_length=20, blank=True)

    class Meta:
        db_table = "cymed_ph_risk_factors"

    def __str__(self):
        return f"{self.factor_name} ({self.factor_type})"


class RiskCategory(BaseModel):
    """Configuration and thresholds for a risk scoring category."""

    category_code = models.CharField(max_length=50, unique=True)
    category_name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    low_threshold = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    moderate_threshold = models.DecimalField(max_digits=5, decimal_places=2, default=30)
    high_threshold = models.DecimalField(max_digits=5, decimal_places=2, default=60)
    very_high_threshold = models.DecimalField(max_digits=5, decimal_places=2, default=80)
    interventions = models.JSONField(default=list)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "cymed_ph_risk_categories"

    def __str__(self):
        return f"{self.category_code} — {self.category_name}"


class RiskAssessment(BaseModel):
    """A holistic risk assessment for a patient combining multiple risk scores."""

    ASSESSMENT_TYPE_CHOICES = [
        ("automated", "Automated"),
        ("manual", "Manual"),
        ("combined", "Combined"),
    ]
    STATUS_CHOICES = [
        ("pending_review", "Pending Review"),
        ("acknowledged", "Acknowledged"),
        ("acted_upon", "Acted Upon"),
        ("archived", "Archived"),
    ]

    patient_id = models.UUIDField(db_index=True)
    assessment_type = models.CharField(
        max_length=20, choices=ASSESSMENT_TYPE_CHOICES, default="automated"
    )
    assessment_date = models.DateField()
    overall_risk_level = models.CharField(max_length=15, choices=RISK_LEVEL_CHOICES)
    overall_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    assessor_user_id = models.UUIDField(null=True, blank=True)
    recommendations = models.JSONField(default=list)
    next_assessment_date = models.DateField(null=True, blank=True)
    is_ai_generated = models.BooleanField(default=False)
    is_advisory_only = models.BooleanField(default=True, editable=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending_review")
    acknowledged_by_user_id = models.UUIDField(null=True, blank=True)

    class Meta:
        db_table = "cymed_ph_risk_assessments"

    def __str__(self):
        return (
            f"Assessment {self.overall_risk_level} — patient {self.patient_id} "
            f"on {self.assessment_date}"
        )
