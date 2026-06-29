from django.db import models
from django.utils import timezone

from platform.common.models import BaseModel, SoftDeleteMixin
from products.cymed.core.encounters.models import Encounter
from products.cymed.core.patients.models import Patient


class Condition(BaseModel, SoftDeleteMixin):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="conditions")
    encounter = models.ForeignKey(
        Encounter, on_delete=models.SET_NULL, null=True, blank=True, related_name="conditions"
    )
    code = models.CharField(max_length=100, db_index=True)  # ICD-11 stem/cluster or SNOMED-CT code
    display = models.CharField(max_length=255)
    system = models.CharField(max_length=50, choices=[("icd11", "ICD-11"), ("snomed", "SNOMED-CT")])
    clinical_status = models.CharField(
        max_length=30,
        choices=[
            ("active", "Active"),
            ("inactive", "Inactive"),
            ("remission", "Remission"),
            ("resolved", "Resolved"),
        ],
        default="active",
    )
    verification_status = models.CharField(
        max_length=30,
        choices=[
            ("provisional", "Provisional"),
            ("confirmed", "Confirmed"),
            ("refuted", "Refuted"),
        ],
        default="confirmed",
    )
    onset_date = models.DateField(null=True, blank=True)
    recorded_at = models.DateTimeField(default=timezone.now)
    recorded_by = models.CharField(max_length=255)

    class Meta:
        db_table = "cymed_clinical_conditions"
        ordering = ["-recorded_at"]

    def __str__(self) -> str:
        return f"{self.display} ({self.code})"


class Allergy(BaseModel):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="allergies")
    category = models.CharField(
        max_length=30,
        choices=[
            ("food", "Food Allergy"),
            ("medication", "Medication Allergy"),
            ("environment", "Environmental Allergy"),
            ("biologic", "Biologic Allergy"),
        ],
    )
    substance_code = models.CharField(max_length=100)  # SNOMED or RxNorm
    substance_display = models.CharField(max_length=255)
    clinical_status = models.CharField(
        max_length=30, choices=[("active", "Active"), ("inactive", "Inactive")], default="active"
    )
    recorded_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "cymed_clinical_allergies"


class AllergyReaction(BaseModel):
    allergy = models.ForeignKey(Allergy, on_delete=models.CASCADE, related_name="reactions")
    manifestation_code = models.CharField(max_length=100)  # SNOMED
    severity = models.CharField(
        max_length=20, choices=[("mild", "Mild"), ("moderate", "Moderate"), ("severe", "Severe")]
    )

    class Meta:
        db_table = "cymed_clinical_allergy_reactions"


class VitalSignType(models.TextChoices):
    TEMPERATURE = "temperature", "Temperature (C)"
    HEART_RATE = "heart_rate", "Heart Rate (bpm)"
    RESPIRATORY_RATE = "respiratory_rate", "Respiratory Rate (rpm)"
    SYSTOLIC_BP = "systolic_bp", "Systolic Blood Pressure (mmHg)"
    DIASTOLIC_BP = "diastolic_bp", "Diastolic Blood Pressure (mmHg)"
    OXYGEN_SATURATION = "oxygen_saturation", "Oxygen Saturation (%)"
    WEIGHT = "weight", "Weight (kg)"
    HEIGHT = "height", "Height (cm)"


class VitalSign(BaseModel):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="vitals")
    encounter = models.ForeignKey(Encounter, on_delete=models.CASCADE, related_name="vitals")
    taken_at = models.DateTimeField(default=timezone.now)
    taken_by = models.CharField(max_length=255)
    type = models.CharField(max_length=30, choices=VitalSignType.choices)
    value = models.DecimalField(max_digits=6, decimal_places=2)
    unit = models.CharField(max_length=20)

    class Meta:
        db_table = "cymed_clinical_vitals"
        ordering = ["-taken_at"]


class Observation(BaseModel):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="observations")
    encounter = models.ForeignKey(Encounter, on_delete=models.CASCADE, related_name="observations")
    code = models.CharField(max_length=100, db_index=True)  # LOINC code
    display = models.CharField(max_length=255)
    value_quantity = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    value_string = models.TextField(blank=True)
    unit = models.CharField(max_length=50, blank=True)
    reference_range = models.CharField(max_length=100, blank=True)
    status = models.CharField(
        max_length=30,
        choices=[("preliminary", "Preliminary"), ("final", "Final"), ("amended", "Amended")],
        default="final",
    )

    class Meta:
        db_table = "cymed_clinical_observations"


class Immunization(BaseModel):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="immunizations")
    vaccine_code = models.CharField(max_length=100)
    vaccine_display = models.CharField(max_length=255)
    administered_date = models.DateField()
    status = models.CharField(
        max_length=30,
        choices=[("completed", "Completed"), ("not_done", "Not Done")],
        default="completed",
    )

    class Meta:
        db_table = "cymed_clinical_immunizations"


class RiskFactor(BaseModel):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="risk_factors")
    risk_code = models.CharField(max_length=100)
    risk_display = models.CharField(max_length=255)
    severity = models.CharField(
        max_length=20, choices=[("low", "Low"), ("medium", "Medium"), ("high", "High")]
    )

    class Meta:
        db_table = "cymed_clinical_risk_factors"


class ClinicalFlag(BaseModel):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="flags")
    flag_text = models.CharField(max_length=255)
    category = models.CharField(
        max_length=30,
        choices=[
            ("security", "Security Flag"),
            ("medical", "Medical Warning Flag"),
            ("administrative", "Administrative Flag"),
        ],
        default="medical",
    )
    status = models.CharField(
        max_length=20, choices=[("active", "Active"), ("inactive", "Inactive")], default="active"
    )

    class Meta:
        db_table = "cymed_clinical_flags"
