from django.db import models
from platform.common.models import BaseModel


ACUITY_LEVEL_CHOICES = [
    (1, "Level 1 — Stable (HPPD 4.0h)"),
    (2, "Level 2 — Moderate Care (HPPD 6.5h)"),
    (3, "Level 3 — High Dependency (HPPD 9.5h)"),
    (4, "Level 4 — Intensive Care (HPPD 18.0-24.0h)"),
]

WARD_TYPE_CHOICES = [
    ("icu", "Intensive Care Unit (ICU)"),
    ("nicu", "Neonatal ICU (NICU)"),
    ("ed", "Emergency Department (ED)"),
    ("ld", "Labor & Delivery (L&D)"),
    ("pediatrics", "Pediatrics"),
    ("med_surg", "Medical-Surgical"),
    ("or", "Operating Room"),
    ("general", "General"),
]

VALIDATION_STATUS_CHOICES = [
    ("passed", "Passed"),
    ("failed", "Failed"),
    ("warning", "Warning"),
]


HPPD_BY_LEVEL = {1: 4.0, 2: 6.5, 3: 9.5, 4: 21.0}


class PatientAcuityScore(BaseModel):
    class Meta:
        app_label = "cymed_hwm_acuity"
        db_table = "cymed_hwm_acuity_patient_score"

    # Patient ID from CyMed Core — no model FK
    patient_id = models.UUIDField(db_index=True)
    ward_id = models.UUIDField(db_index=True)
    facility_id = models.UUIDField(db_index=True)

    acuity_level = models.PositiveSmallIntegerField(choices=ACUITY_LEVEL_CHOICES)
    news2_score = models.PositiveSmallIntegerField(null=True, blank=True)
    hppd_target = models.DecimalField(max_digits=5, decimal_places=1)
    scored_at = models.DateTimeField()
    scored_by_id = models.UUIDField(null=True, blank=True)

    def __str__(self):
        return f"Acuity L{self.acuity_level} for patient {self.patient_id}"


class WardCoverageRequirement(BaseModel):
    class Meta:
        app_label = "cymed_hwm_acuity"
        db_table = "cymed_hwm_acuity_coverage_req"
        unique_together = [["tenant_id", "facility_id", "ward_type"]]

    facility_id = models.UUIDField(db_index=True)
    ward_type = models.CharField(max_length=20, choices=WARD_TYPE_CHOICES)
    # Ratio stored as nurse count per patient count (numerator = nurse, denominator = patients)
    day_ratio_nurse = models.PositiveSmallIntegerField(default=1)
    day_ratio_patients = models.PositiveSmallIntegerField(default=4)
    night_ratio_nurse = models.PositiveSmallIntegerField(default=1)
    night_ratio_patients = models.PositiveSmallIntegerField(default=6)
    min_physician_on_site = models.PositiveSmallIntegerField(default=1)
    physician_coverage_24_7 = models.BooleanField(default=False)
    # Percentage of senior nurses required (0-100)
    min_senior_nurse_pct = models.PositiveSmallIntegerField(default=30)
    specialty_cert_required_100pct = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.ward_type} coverage req — facility {self.facility_id}"


class CoverageValidationRun(BaseModel):
    class Meta:
        app_label = "cymed_hwm_acuity"
        db_table = "cymed_hwm_acuity_validation_run"

    roster_cycle_id = models.UUIDField(db_index=True)
    facility_id = models.UUIDField(db_index=True)
    validated_at = models.DateTimeField(auto_now_add=True)
    overall_status = models.CharField(max_length=10, choices=VALIDATION_STATUS_CHOICES)
    issues = models.JSONField(default=list)
    slots_checked = models.PositiveIntegerField(default=0)
    slots_failed = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"Validation run {self.roster_cycle_id} — {self.overall_status}"


class SkillMixValidation(BaseModel):
    class Meta:
        app_label = "cymed_hwm_acuity"
        db_table = "cymed_hwm_acuity_skill_mix"

    roster_cycle_id = models.UUIDField(db_index=True)
    ward_id = models.UUIDField(db_index=True)
    slot_date = models.DateField()
    shift_type = models.CharField(max_length=20)
    charge_nurse_present = models.BooleanField(default=False)
    total_nurses_scheduled = models.PositiveSmallIntegerField(default=0)
    senior_nurse_count = models.PositiveSmallIntegerField(default=0)
    senior_nurse_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    specialty_cert_pct = models.DecimalField(max_digits=5, decimal_places=2, default=100)
    passed = models.BooleanField(default=False)
    failure_reasons = models.JSONField(default=list)

    def __str__(self):
        return f"Skill mix {self.slot_date} ward {self.ward_id} — {'PASS' if self.passed else 'FAIL'}"
