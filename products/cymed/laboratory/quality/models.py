"""
CyMed Laboratory â€” Quality Management
QC rules (Westgard), QC runs, failure detection, proficiency testing.
"""
from django.db import models
from platform.common.models import BaseModel


class QCLevel(models.TextChoices):
    L1 = "L1", "Level 1 (Low Normal)"
    L2 = "L2", "Level 2 (Normal)"
    L3 = "L3", "Level 3 (High)"
    L4 = "L4", "Level 4 (Pathological)"


class QualityRule(BaseModel):
    """Westgard or custom QC rule applied to a test/analyzer combination."""
    RULE_TYPES = [
        ("12s", "1â‚‚s â€” Warning: >2 SD"),
        ("13s", "1â‚ƒs â€” Rejection: >3 SD"),
        ("22s", "2â‚‚s â€” Rejection: 2 consecutive >2 SD same direction"),
        ("r4s", "Râ‚„s â€” Rejection: Range >4 SD between controls"),
        ("41s", "4â‚s â€” Rejection: 4 consecutive >1 SD same direction"),
        ("10x", "10x â€” Rejection: 10 consecutive on same side of mean"),
        ("custom", "Custom Rule"),
    ]

    name = models.CharField(max_length=100)
    rule_type = models.CharField(max_length=20, choices=RULE_TYPES)
    test = models.ForeignKey("lab_orders.LabTest", on_delete=models.CASCADE, related_name="qc_rules", null=True, blank=True)
    analyzer = models.ForeignKey("lab_worklists.Analyzer", on_delete=models.SET_NULL, null=True, blank=True, related_name="qc_rules")
    parameters = models.JSONField(default=dict)   # {"sd_multiplier": 2, "consecutive_count": 4}
    is_warning = models.BooleanField(default=False)
    is_rejection = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    description = models.TextField(blank=True)

    class Meta:
        db_table = "cymed_lab_quality_rules"


class QualityControl(BaseModel):
    """QC material/reagent lot with expected statistical parameters."""
    test = models.ForeignKey("lab_orders.LabTest", on_delete=models.CASCADE, related_name="qc_materials")
    analyzer = models.ForeignKey("lab_worklists.Analyzer", on_delete=models.SET_NULL, null=True, blank=True, related_name="qc_materials")
    lot_number = models.CharField(max_length=100)
    product_name = models.CharField(max_length=255, blank=True)
    manufacturer = models.CharField(max_length=100, blank=True)
    level = models.CharField(max_length=5, choices=QCLevel.choices, default=QCLevel.L2)
    target_mean = models.DecimalField(max_digits=18, decimal_places=6)
    target_sd = models.DecimalField(max_digits=18, decimal_places=6)
    allowable_sd_multiplier = models.DecimalField(max_digits=4, decimal_places=1, default=2)
    unit = models.CharField(max_length=50, blank=True)
    expiry_date = models.DateField()
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "cymed_lab_quality_controls"
        unique_together = [("tenant_id", "test", "lot_number", "level")]


class QualityRun(BaseModel):
    """Single QC run entry â€” measured value compared against expected range."""
    qc = models.ForeignKey(QualityControl, on_delete=models.CASCADE, related_name="runs")
    run_date = models.DateField()
    run_time = models.TimeField()
    technologist_id = models.UUIDField()
    analyzer_id = models.UUIDField(null=True, blank=True)
    measured_value = models.DecimalField(max_digits=18, decimal_places=6)
    z_score = models.DecimalField(max_digits=8, decimal_places=4, null=True, blank=True)
    passed = models.BooleanField()
    is_warning = models.BooleanField(default=False)
    is_rejection = models.BooleanField(default=False)
    rules_triggered = models.JSONField(default=list)   # ["13s", "22s"]
    comments = models.CharField(max_length=500, blank=True)

    class Meta:
        db_table = "cymed_lab_quality_runs"
        indexes = [models.Index(fields=["qc", "run_date", "passed"])]


class QualityFailure(BaseModel):
    """Investigation and corrective action record for a QC rejection."""
    STATUS_CHOICES = [
        ("open", "Open"),
        ("investigating", "Under Investigation"),
        ("corrective_action", "Corrective Action Taken"),
        ("resolved", "Resolved"),
        ("escalated", "Escalated"),
    ]

    qc_run = models.ForeignKey(QualityRun, on_delete=models.CASCADE, related_name="failures")
    failure_type = models.CharField(max_length=100, blank=True)
    root_cause = models.TextField(blank=True)
    corrective_action = models.TextField(blank=True)
    action_taken_by = models.UUIDField(null=True, blank=True)
    action_taken_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.UUIDField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default="open")
    patient_results_affected = models.BooleanField(default=False)
    results_held_count = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "cymed_lab_quality_failures"


class ProficiencyTest(BaseModel):
    """External quality assurance / proficiency testing program participation."""
    STATUS_CHOICES = [
        ("enrolled", "Enrolled"),
        ("sample_received", "Sample Received"),
        ("testing", "Testing in Progress"),
        ("submitted", "Results Submitted"),
        ("graded", "Graded"),
    ]

    program_name = models.CharField(max_length=255)
    program_provider = models.CharField(max_length=255, blank=True)   # CAP, RCPAQAP, NEQAS
    testing_period = models.CharField(max_length=50)     # e.g., "2026-Q1"
    start_date = models.DateField()
    submission_date = models.DateField(null=True, blank=True)
    deadline_date = models.DateField(null=True, blank=True)
    test_list = models.JSONField(default=list)            # analytes included
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default="enrolled")
    score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    score_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    grade = models.CharField(max_length=20, blank=True)
    report_url = models.URLField(max_length=1000, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "cymed_lab_proficiency_tests"
