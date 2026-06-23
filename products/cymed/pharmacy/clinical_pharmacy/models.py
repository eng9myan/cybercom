"""
CyMed Pharmacy — Clinical Pharmacy Module
Models: MedicationReview, ClinicalIntervention, PharmacistRecommendation,
        MedicationTherapyManagement

Capabilities: Clinical Review, Drug Utilization Review, Medication Optimization,
              Clinical Recommendations, Polypharmacy Risk Detection (CyAI)

Terminology: SNOMED, ICD-11 via TerminologyService.
CyAI: Polypharmacy risk, adherence analysis — pharmacist makes all decisions.
"""
from django.db import models
from platform.common.models import BaseModel


class ReviewStatus(models.TextChoices):
    SCHEDULED = "scheduled", "Scheduled"
    IN_PROGRESS = "in_progress", "In Progress"
    COMPLETED = "completed", "Completed"
    CANCELLED = "cancelled", "Cancelled"


class MedicationReview(BaseModel):
    """
    Formal clinical pharmacist review of a patient's complete medication regimen.
    Supports: Drug Utilization Review (DUR), Comprehensive Medication Review (CMR),
              Targeted Medication Review (TMR).
    CyAI identifies polypharmacy risks — pharmacist validates and acts.
    """
    REVIEW_TYPES = [
        ("dur", "Drug Utilization Review"),
        ("cmr", "Comprehensive Medication Review"),
        ("tmr", "Targeted Medication Review"),
        ("admission", "Admission Medication Review"),
        ("discharge", "Discharge Medication Review"),
        ("transfer", "Transfer Medication Review"),
    ]

    patient_id = models.UUIDField(db_index=True)
    encounter_id = models.UUIDField(null=True, blank=True)
    admission_id = models.UUIDField(null=True, blank=True)
    pharmacist_id = models.UUIDField(db_index=True)
    review_type = models.CharField(max_length=30, choices=REVIEW_TYPES, default="dur")
    status = models.CharField(max_length=30, choices=ReviewStatus.choices, default=ReviewStatus.SCHEDULED)
    scheduled_date = models.DateField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    # Scope
    medications_reviewed = models.JSONField(default=list)             # Drug codes reviewed
    diagnoses_considered = models.JSONField(default=list)             # ICD-11 codes
    lab_values_considered = models.JSONField(default=dict)            # lab code -> value pairs

    # Assessment
    polypharmacy_risk = models.CharField(
        max_length=20,
        choices=[("low", "Low"), ("moderate", "Moderate"), ("high", "High"), ("critical", "Critical")],
        default="low"
    )
    ai_polypharmacy_score = models.FloatField(default=0.0)           # CyAI score
    adherence_score = models.FloatField(null=True, blank=True)       # CyAI analysis
    clinical_summary = models.TextField(blank=True)
    therapy_gaps = models.TextField(blank=True)
    optimization_notes = models.TextField(blank=True)

    # Outcomes
    interventions_count = models.PositiveSmallIntegerField(default=0)
    recommendations_count = models.PositiveSmallIntegerField(default=0)
    accepted_recommendations = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = "cymed_clinical_medication_reviews"
        indexes = [
            models.Index(fields=["patient_id", "status"]),
            models.Index(fields=["pharmacist_id", "scheduled_date"]),
            models.Index(fields=["tenant_id", "review_type"]),
        ]


class ClinicalIntervention(BaseModel):
    """
    Clinical pharmacist intervention record.
    Documents issues identified and actions taken during clinical review.
    """
    INTERVENTION_TYPES = [
        ("dose_optimization", "Dose Optimization"),
        ("drug_substitution", "Drug Substitution"),
        ("therapy_addition", "Therapy Addition"),
        ("therapy_discontinuation", "Therapy Discontinuation"),
        ("drug_interaction_resolution", "Drug Interaction Resolution"),
        ("allergy_resolution", "Allergy Conflict Resolution"),
        ("compliance_counseling", "Compliance Counseling"),
        ("cost_optimization", "Cost Optimization"),
        ("route_change", "Route of Administration Change"),
        ("monitoring_recommendation", "Monitoring Recommendation"),
        ("other", "Other"),
    ]
    OUTCOME_CHOICES = [
        ("accepted", "Accepted by Prescriber"),
        ("partially_accepted", "Partially Accepted"),
        ("declined", "Declined by Prescriber"),
        ("no_action_needed", "No Action Needed"),
        ("pending", "Pending Prescriber Response"),
    ]

    review = models.ForeignKey(MedicationReview, on_delete=models.CASCADE, related_name="interventions")
    patient_id = models.UUIDField(db_index=True)
    pharmacist_id = models.UUIDField()
    prescriber_id = models.UUIDField(null=True, blank=True)

    intervention_type = models.CharField(max_length=50, choices=INTERVENTION_TYPES)
    problem_identified = models.TextField()
    intervention_action = models.TextField()
    drug_code = models.CharField(max_length=100, blank=True)
    drug_name = models.CharField(max_length=500, blank=True)
    icd11_code = models.CharField(max_length=20, blank=True)          # Related diagnosis
    outcome = models.CharField(max_length=30, choices=OUTCOME_CHOICES, default="pending")
    clinical_significance = models.CharField(
        max_length=20,
        choices=[("minor", "Minor"), ("moderate", "Moderate"), ("major", "Major")],
        default="moderate"
    )
    outcome_notes = models.TextField(blank=True)
    cost_saving_estimate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    intervened_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "cymed_clinical_interventions"
        ordering = ["-intervened_at"]
        indexes = [models.Index(fields=["patient_id", "outcome"])]


class PharmacistRecommendation(BaseModel):
    """
    Formal clinical recommendation from pharmacist to prescriber or care team.
    Tracked for acceptance, rejection, and clinical outcomes.
    """
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("submitted", "Submitted to Prescriber"),
        ("accepted", "Accepted"),
        ("rejected", "Rejected"),
        ("withdrawn", "Withdrawn"),
    ]

    review = models.ForeignKey(
        MedicationReview, on_delete=models.CASCADE, related_name="recommendations",
        null=True, blank=True
    )
    patient_id = models.UUIDField(db_index=True)
    pharmacist_id = models.UUIDField()
    prescriber_id = models.UUIDField(null=True, blank=True)
    recommendation_text = models.TextField()
    rationale = models.TextField()
    priority = models.CharField(
        max_length=20,
        choices=[("low", "Low"), ("moderate", "Moderate"), ("high", "High"), ("urgent", "Urgent")],
        default="moderate"
    )
    drug_code = models.CharField(max_length=100, blank=True)
    drug_name = models.CharField(max_length=500, blank=True)
    evidence_references = models.JSONField(default=list)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default="draft")
    prescriber_response = models.TextField(blank=True)
    responded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "cymed_pharmacist_recommendations"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["patient_id", "status"])]


class MedicationTherapyManagement(BaseModel):
    """
    MTM (Medication Therapy Management) program enrollment and session tracking.
    Used in retail pharmacy and chronic disease management programs.
    """
    SESSION_TYPES = [
        ("initial", "Initial Assessment"),
        ("follow_up", "Follow-Up Session"),
        ("annual", "Annual Comprehensive Review"),
        ("targeted", "Targeted Intervention"),
    ]

    patient_id = models.UUIDField(db_index=True)
    pharmacist_id = models.UUIDField()
    session_type = models.CharField(max_length=30, choices=SESSION_TYPES, default="initial")
    scheduled_date = models.DateField()
    completed_at = models.DateTimeField(null=True, blank=True)
    duration_minutes = models.PositiveSmallIntegerField(default=0)
    program_name = models.CharField(max_length=200, blank=True)       # e.g., "Diabetes MTM"
    conditions_addressed = models.JSONField(default=list)             # ICD-11 codes
    medications_addressed = models.JSONField(default=list)            # Drug codes
    goals_set = models.TextField(blank=True)
    barriers_identified = models.TextField(blank=True)
    action_plan = models.TextField(blank=True)
    follow_up_date = models.DateField(null=True, blank=True)
    patient_satisfaction = models.PositiveSmallIntegerField(null=True, blank=True)  # 1–5
    billing_code = models.CharField(max_length=50, blank=True)        # CPT code for billing
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "cymed_medication_therapy_mgmt"
        ordering = ["-scheduled_date"]
        indexes = [models.Index(fields=["patient_id", "session_type"])]
