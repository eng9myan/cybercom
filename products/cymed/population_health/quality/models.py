"""
CyMed Population Health — Quality
Covers: QualityMeasure, QualityMeasureResult, QualityImprovement, ClinicalAudit
Terminology: ICD-11 and LOINC codes resolved via TerminologyService.
"""
from django.db import models
from platform.common.models import BaseModel


class QualityMeasure(BaseModel):
    """A clinical quality measure definition (process, outcome, structure, composite)."""
    MEASURE_TYPE_CHOICES = [
        ("process", "Process"),
        ("outcome", "Outcome"),
        ("structure", "Structure"),
        ("composite", "Composite"),
        ("patient_reported", "Patient Reported"),
    ]
    REPORTING_PERIOD_CHOICES = [
        ("monthly", "Monthly"),
        ("quarterly", "Quarterly"),
        ("annual", "Annual"),
    ]

    measure_code = models.CharField(max_length=50, unique=True)
    measure_name = models.CharField(max_length=200)
    measure_type = models.CharField(max_length=20, choices=MEASURE_TYPE_CHOICES)
    description = models.TextField(blank=True)
    numerator_definition = models.JSONField(default=dict)
    denominator_definition = models.JSONField(default=dict)
    target_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    benchmark_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    is_national = models.BooleanField(default=False)
    reporting_period = models.CharField(
        max_length=20, choices=REPORTING_PERIOD_CHOICES, default="annual"
    )
    related_icd11_codes = models.JSONField(default=list)
    loinc_codes = models.JSONField(default=list)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "cymed_ph_qual_measures"

    def __str__(self):
        return f"{self.measure_code} — {self.measure_name}"


class QualityMeasureResult(BaseModel):
    """A calculated performance result for a quality measure in a given period and facility."""

    measure = models.ForeignKey(
        QualityMeasure, on_delete=models.PROTECT, related_name="results"
    )
    facility_id = models.UUIDField(db_index=True)
    period_start = models.DateField()
    period_end = models.DateField()
    numerator = models.PositiveIntegerField(default=0)
    denominator = models.PositiveIntegerField(default=0)
    performance_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    benchmark_rate = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    meets_target = models.BooleanField(default=False)
    calculated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "cymed_ph_qual_results"
        unique_together = [["tenant_id", "measure", "facility_id", "period_start", "period_end"]]

    def __str__(self):
        return (
            f"{self.measure} — facility {self.facility_id} "
            f"[{self.period_start} to {self.period_end}]"
        )


class QualityImprovement(BaseModel):
    """A quality improvement initiative linked to a measure result."""
    INTERVENTION_TYPE_CHOICES = [
        ("process_change", "Process Change"),
        ("training", "Training"),
        ("technology", "Technology"),
        ("policy", "Policy"),
        ("care_pathway", "Care Pathway"),
        ("audit_feedback", "Audit and Feedback"),
        ("other", "Other"),
    ]
    STATUS_CHOICES = [
        ("planned", "Planned"),
        ("active", "Active"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]

    measure_result = models.ForeignKey(
        QualityMeasureResult, on_delete=models.CASCADE, related_name="improvements"
    )
    intervention_type = models.CharField(max_length=50, choices=INTERVENTION_TYPE_CHOICES)
    intervention_description = models.TextField()
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="planned")
    expected_improvement = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    actual_improvement = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    responsible_user_id = models.UUIDField(null=True, blank=True)

    class Meta:
        db_table = "cymed_ph_qual_improvements"

    def __str__(self):
        return f"{self.intervention_type} [{self.status}] — result {self.measure_result_id}"


class ClinicalAudit(BaseModel):
    """A structured clinical audit evaluating compliance with defined criteria."""
    AUDIT_TYPE_CHOICES = [
        ("clinical_practice", "Clinical Practice"),
        ("medication", "Medication"),
        ("infection_control", "Infection Control"),
        ("documentation", "Documentation"),
        ("patient_safety", "Patient Safety"),
        ("outcome", "Outcome"),
        ("process", "Process"),
    ]
    STATUS_CHOICES = [
        ("planned", "Planned"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("reported", "Reported"),
    ]

    audit_name = models.CharField(max_length=200)
    audit_type = models.CharField(max_length=30, choices=AUDIT_TYPE_CHOICES)
    facility_id = models.UUIDField(db_index=True)
    period_start = models.DateField()
    period_end = models.DateField()
    audit_criteria = models.JSONField(default=list)
    auditor_id = models.UUIDField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="planned")
    sample_size = models.PositiveIntegerField(default=0)
    compliant_count = models.PositiveIntegerField(default=0)
    compliance_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    findings = models.JSONField(default=list)
    recommendations = models.JSONField(default=list)

    class Meta:
        db_table = "cymed_ph_qual_audits"

    def __str__(self):
        return f"{self.audit_name} [{self.status}] — facility {self.facility_id}"
