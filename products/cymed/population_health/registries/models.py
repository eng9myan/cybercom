from django.db import models

from platform.common.models import BaseModel

REGISTRY_TYPE_CHOICES = [
    ("cancer", "Cancer"),
    ("diabetes", "Diabetes"),
    ("cardiology", "Cardiology"),
    ("stroke", "Stroke"),
    ("maternal", "Maternal"),
    ("child_health", "Child Health"),
    ("rare_disease", "Rare Disease"),
    ("mental_health", "Mental Health"),
    ("vaccination", "Vaccination"),
    ("chronic_kidney", "Chronic Kidney"),
    ("hypertension", "Hypertension"),
    ("other", "Other"),
]

PATIENT_STATUS_CHOICES = [
    ("active", "Active"),
    ("inactive", "Inactive"),
    ("deceased", "Deceased"),
    ("transferred", "Transferred"),
    ("withdrawn", "Withdrawn"),
]

ENROLLMENT_SOURCE_CHOICES = [
    ("clinical", "Clinical"),
    ("laboratory", "Laboratory"),
    ("imaging", "Imaging"),
    ("pharmacy", "Pharmacy"),
    ("self_referral", "Self Referral"),
    ("external", "External"),
]

OUTCOME_TYPE_CHOICES = [
    ("remission", "Remission"),
    ("progression", "Progression"),
    ("complication", "Complication"),
    ("recovery", "Recovery"),
    ("death", "Death"),
    ("transfer", "Transfer"),
    ("lost_to_followup", "Lost to Follow-up"),
    ("other", "Other"),
]

SEVERITY_CHOICES = [
    ("mild", "Mild"),
    ("moderate", "Moderate"),
    ("severe", "Severe"),
    ("critical", "Critical"),
]


class DiseaseRegistry(BaseModel):
    class Meta:
        app_label = "cymed_ph_registries"
        db_table = "cymed_ph_reg_registries"

    name = models.CharField(max_length=200)
    registry_type = models.CharField(max_length=30, choices=REGISTRY_TYPE_CHOICES)
    description = models.TextField(blank=True)
    # ICD-11 codes sourced from TerminologyService -- no local table
    icd11_codes = models.JSONField(default=list)
    is_national = models.BooleanField(default=False)
    managing_authority = models.CharField(max_length=200, blank=True)
    start_date = models.DateField()
    is_active = models.BooleanField(default=True)
    registry_code = models.CharField(max_length=50, unique=True, null=True, blank=True)
    fhir_list_id = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.registry_type})"


class RegistryPatient(BaseModel):
    class Meta:
        app_label = "cymed_ph_registries"
        db_table = "cymed_ph_reg_patients"
        unique_together = [["tenant_id", "registry", "patient_id"]]

    registry = models.ForeignKey(
        DiseaseRegistry,
        on_delete=models.PROTECT,
        related_name="patients",
    )
    patient_id = models.UUIDField(db_index=True)
    enrollment_date = models.DateField()
    status = models.CharField(max_length=20, choices=PATIENT_STATUS_CHOICES, default="active")
    # Hashed national ID used for cross-registry deduplication
    national_id_hash = models.CharField(max_length=200, blank=True)
    enrollment_source = models.CharField(
        max_length=30, choices=ENROLLMENT_SOURCE_CHOICES, default="clinical"
    )
    # ICD-11 code for the registry condition -- sourced from TerminologyService
    primary_icd11_code = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f"Patient {self.patient_id} in {self.registry_id}"


class RegistryEnrollment(BaseModel):
    class Meta:
        app_label = "cymed_ph_registries"
        db_table = "cymed_ph_reg_enrollments"

    registry_patient = models.ForeignKey(
        RegistryPatient,
        on_delete=models.CASCADE,
        related_name="enrollments",
    )
    enrolling_provider_id = models.UUIDField(null=True, blank=True)
    enrolling_facility_id = models.UUIDField(null=True, blank=True)
    # List of criteria codes met at time of enrollment
    enrollment_criteria_met = models.JSONField(default=list)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"Enrollment for {self.registry_patient_id}"


class RegistryStatus(BaseModel):
    class Meta:
        app_label = "cymed_ph_registries"
        db_table = "cymed_ph_reg_status_history"

    registry_patient = models.ForeignKey(
        RegistryPatient,
        on_delete=models.CASCADE,
        related_name="status_history",
    )
    status_date = models.DateField()
    status = models.CharField(max_length=20, choices=PATIENT_STATUS_CHOICES)
    changed_by_user_id = models.UUIDField(null=True, blank=True)
    reason = models.TextField(blank=True)

    def __str__(self):
        return f"Status {self.status} on {self.status_date}"


class RegistryOutcome(BaseModel):
    class Meta:
        app_label = "cymed_ph_registries"
        db_table = "cymed_ph_reg_outcomes"

    registry_patient = models.ForeignKey(
        RegistryPatient,
        on_delete=models.CASCADE,
        related_name="outcomes",
    )
    outcome_type = models.CharField(max_length=30, choices=OUTCOME_TYPE_CHOICES)
    outcome_date = models.DateField()
    # ICD-11 code for outcome condition -- sourced from TerminologyService
    icd11_code = models.CharField(max_length=20, blank=True)
    outcome_description = models.TextField(blank=True)
    reporting_provider_id = models.UUIDField(null=True, blank=True)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, blank=True)

    def __str__(self):
        return f"Outcome {self.outcome_type} on {self.outcome_date}"
