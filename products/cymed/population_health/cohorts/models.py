"""
CyMed Population Health — Cohorts
Covers: Cohort, CohortMember, CohortOutcome, CohortAnalysis
Terminology: ICD-11 codes resolved via TerminologyService.
AI-generated analyses are advisory only (is_advisory_only=True, editable=False).
"""
from django.db import models
from platform.common.models import BaseModel


class Cohort(BaseModel):
    """A defined group of patients sharing common clinical or demographic characteristics."""
    COHORT_TYPE_CHOICES = [
        ("study", "Study"),
        ("quality", "Quality"),
        ("population", "Population"),
        ("intervention", "Intervention"),
        ("control", "Control"),
        ("registry", "Registry"),
        ("benchmark", "Benchmark"),
    ]

    name = models.CharField(max_length=200)
    cohort_type = models.CharField(max_length=20, choices=COHORT_TYPE_CHOICES)
    description = models.TextField(blank=True)
    inclusion_criteria = models.JSONField(default=dict)
    exclusion_criteria = models.JSONField(default=dict)
    created_by_user_id = models.UUIDField()
    patient_count = models.PositiveIntegerField(default=0)
    is_dynamic = models.BooleanField(default=True)
    last_updated_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "cymed_ph_coh_cohorts"

    def __str__(self):
        return f"{self.name} ({self.cohort_type})"


class CohortMember(BaseModel):
    """A patient's membership record within a cohort."""

    cohort = models.ForeignKey(
        Cohort, on_delete=models.CASCADE, related_name="members"
    )
    patient_id = models.UUIDField(db_index=True)
    joined_at = models.DateTimeField(auto_now_add=True)
    removed_at = models.DateTimeField(null=True, blank=True)
    removal_reason = models.CharField(max_length=200, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "cymed_ph_coh_members"
        unique_together = [["tenant_id", "cohort", "patient_id"]]

    def __str__(self):
        return f"Patient {self.patient_id} in cohort {self.cohort_id}"


class CohortOutcome(BaseModel):
    """A measured outcome for a patient within a cohort context."""
    OUTCOME_TYPE_CHOICES = [
        ("clinical", "Clinical"),
        ("quality", "Quality"),
        ("cost", "Cost"),
        ("utilization", "Utilization"),
        ("satisfaction", "Satisfaction"),
    ]

    cohort = models.ForeignKey(
        Cohort, on_delete=models.CASCADE, related_name="outcomes"
    )
    patient_id = models.UUIDField(db_index=True)
    outcome_name = models.CharField(max_length=200)
    outcome_type = models.CharField(max_length=30, choices=OUTCOME_TYPE_CHOICES)
    measurement_date = models.DateField()
    value = models.CharField(max_length=200, blank=True)
    unit = models.CharField(max_length=50, blank=True)
    icd11_code = models.CharField(max_length=20, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "cymed_ph_coh_outcomes"

    def __str__(self):
        return f"{self.outcome_name} [{self.outcome_type}] — patient {self.patient_id}"


class CohortAnalysis(BaseModel):
    """A formal analysis performed on a cohort."""
    ANALYSIS_TYPE_CHOICES = [
        ("descriptive", "Descriptive"),
        ("comparative", "Comparative"),
        ("trend", "Trend"),
        ("outcome", "Outcome"),
        ("predictive", "Predictive"),
        ("survival", "Survival"),
    ]

    cohort = models.ForeignKey(
        Cohort, on_delete=models.PROTECT, related_name="analyses"
    )
    analysis_type = models.CharField(max_length=30, choices=ANALYSIS_TYPE_CHOICES)
    analysis_name = models.CharField(max_length=200)
    analysis_date = models.DateField()
    results = models.JSONField(default=dict)
    performed_by_user_id = models.UUIDField(null=True, blank=True)
    is_ai_generated = models.BooleanField(default=False)
    is_advisory_only = models.BooleanField(default=True, editable=False)
    summary = models.TextField(blank=True)

    class Meta:
        db_table = "cymed_ph_coh_analyses"

    def __str__(self):
        return f"{self.analysis_name} ({self.analysis_type}) on cohort {self.cohort_id}"
