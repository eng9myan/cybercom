from django.db import models

from platform.common.models import BaseModel

PROGRAM_TYPE_CHOICES = [
    ("vaccination", "Vaccination"),
    ("screening", "Screening"),
    ("chronic_disease", "Chronic Disease"),
    ("maternal", "Maternal"),
    ("child_health", "Child Health"),
    ("mental_health", "Mental Health"),
    ("cancer", "Cancer"),
    ("nutrition", "Nutrition"),
    ("smoking_cessation", "Smoking Cessation"),
    ("cardiovascular", "Cardiovascular"),
    ("elderly_care", "Elderly Care"),
    ("other", "Other"),
]

PROGRAM_STATUS_CHOICES = [
    ("planning", "Planning"),
    ("active", "Active"),
    ("completed", "Completed"),
    ("suspended", "Suspended"),
]

ENROLLMENT_STATUS_CHOICES = [
    ("active", "Active"),
    ("completed", "Completed"),
    ("withdrawn", "Withdrawn"),
    ("transferred", "Transferred"),
    ("lost_to_followup", "Lost to Follow-up"),
]

OUTCOME_TYPE_CHOICES = [
    ("screening_complete", "Screening Complete"),
    ("vaccination_complete", "Vaccination Complete"),
    ("goal_achieved", "Goal Achieved"),
    ("condition_improved", "Condition Improved"),
    ("hospitalization_avoided", "Hospitalisation Avoided"),
    ("complication_prevented", "Complication Prevented"),
    ("other", "Other"),
]

METRIC_TYPE_CHOICES = [
    ("coverage", "Coverage"),
    ("adherence", "Adherence"),
    ("outcome", "Outcome"),
    ("efficiency", "Efficiency"),
    ("cost_effectiveness", "Cost-Effectiveness"),
    ("patient_satisfaction", "Patient Satisfaction"),
]


class HealthProgram(BaseModel):
    class Meta:
        app_label = "cymed_ph_national_programs"
        db_table = "cymed_ph_prog_programs"

    program_code = models.CharField(max_length=50, unique=True)
    program_name = models.CharField(max_length=200)
    program_type = models.CharField(max_length=30, choices=PROGRAM_TYPE_CHOICES)
    governing_authority = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    target_population_description = models.TextField(blank=True)
    target_age_min = models.PositiveSmallIntegerField(null=True, blank=True)
    target_age_max = models.PositiveSmallIntegerField(null=True, blank=True)
    target_population_size = models.PositiveIntegerField(default=0)
    enrolled_count = models.PositiveIntegerField(default=0)
    completion_count = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=PROGRAM_STATUS_CHOICES, default="planning")
    program_manager_id = models.UUIDField(null=True, blank=True)
    # ICD-11 codes sourced from TerminologyService — no local term table
    related_icd11_codes = models.JSONField(default=list)
    fhir_care_plan_id = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return f"{self.program_code} — {self.program_name}"


class ProgramEnrollment(BaseModel):
    class Meta:
        app_label = "cymed_ph_national_programs"
        db_table = "cymed_ph_prog_enrollments"
        unique_together = [["tenant_id", "program", "patient_id"]]

    program = models.ForeignKey(
        HealthProgram,
        on_delete=models.PROTECT,
        related_name="enrollments",
    )
    patient_id = models.UUIDField(db_index=True)
    enrollment_date = models.DateField()
    enrolled_by_user_id = models.UUIDField(null=True, blank=True)
    enrollment_facility_id = models.UUIDField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=ENROLLMENT_STATUS_CHOICES, default="active")
    notes = models.TextField(blank=True)
    expected_completion_date = models.DateField(null=True, blank=True)
    actual_completion_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"Patient {self.patient_id} in {self.program_id}"


class ProgramOutcome(BaseModel):
    class Meta:
        app_label = "cymed_ph_national_programs"
        db_table = "cymed_ph_prog_outcomes"

    program = models.ForeignKey(
        HealthProgram,
        on_delete=models.PROTECT,
        related_name="outcomes",
    )
    patient_id = models.UUIDField(db_index=True)
    outcome_type = models.CharField(max_length=30, choices=OUTCOME_TYPE_CHOICES)
    outcome_date = models.DateField()
    outcome_value = models.CharField(max_length=200, blank=True)
    outcome_notes = models.TextField(blank=True)
    recording_provider_id = models.UUIDField(null=True, blank=True)
    # ICD-11 code from TerminologyService
    icd11_code = models.CharField(max_length=20, blank=True)
    loinc_code = models.CharField(max_length=30, blank=True)

    def __str__(self):
        return f"Outcome {self.outcome_type} for patient {self.patient_id}"


class ProgramMetric(BaseModel):
    class Meta:
        app_label = "cymed_ph_national_programs"
        db_table = "cymed_ph_prog_metrics"
        unique_together = [["tenant_id", "program", "metric_name", "metric_date"]]

    program = models.ForeignKey(
        HealthProgram,
        on_delete=models.CASCADE,
        related_name="metrics",
    )
    metric_name = models.CharField(max_length=200)
    metric_type = models.CharField(max_length=20, choices=METRIC_TYPE_CHOICES)
    metric_date = models.DateField()
    target_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    actual_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    unit = models.CharField(max_length=50, blank=True)
    meets_target = models.BooleanField(default=False)
    calculation_notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.metric_name} — {self.program_id} ({self.metric_date})"
