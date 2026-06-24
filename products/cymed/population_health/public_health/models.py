from django.db import models
from platform.common.models import BaseModel


GROUP_TYPE_CHOICES = [
    ("geographic", "Geographic"),
    ("demographic", "Demographic"),
    ("clinical", "Clinical"),
    ("risk", "Risk"),
    ("program", "Program"),
    ("chronic_disease", "Chronic Disease"),
    ("insurance", "Insurance"),
]

RISK_TYPE_CHOICES = [
    ("cardiovascular", "Cardiovascular"),
    ("diabetes", "Diabetes"),
    ("cancer", "Cancer"),
    ("respiratory", "Respiratory"),
    ("mental_health", "Mental Health"),
    ("falls", "Falls"),
    ("readmission", "Readmission"),
    ("mortality", "Mortality"),
    ("high_cost", "High Cost"),
]

RISK_LEVEL_CHOICES = [
    ("low", "Low"),
    ("moderate", "Moderate"),
    ("high", "High"),
    ("very_high", "Very High"),
    ("critical", "Critical"),
]

GOAL_TYPE_CHOICES = [
    ("weight_loss", "Weight Loss"),
    ("bp_control", "Blood Pressure Control"),
    ("glucose_control", "Glucose Control"),
    ("smoking_cessation", "Smoking Cessation"),
    ("exercise", "Exercise"),
    ("medication_adherence", "Medication Adherence"),
    ("vaccination", "Vaccination"),
    ("screening", "Screening"),
    ("other", "Other"),
]

GOAL_STATUS_CHOICES = [
    ("active", "Active"),
    ("achieved", "Achieved"),
    ("not_achieved", "Not Achieved"),
    ("abandoned", "Abandoned"),
    ("on_hold", "On Hold"),
]

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
    ("other", "Other"),
]

PROGRAM_STATUS_CHOICES = [
    ("planning", "Planning"),
    ("active", "Active"),
    ("completed", "Completed"),
    ("suspended", "Suspended"),
]

PROVIDER_TYPE_CHOICES = [
    ("physician", "Physician"),
    ("specialist", "Specialist"),
    ("nurse", "Nurse"),
    ("pharmacist", "Pharmacist"),
    ("therapist", "Therapist"),
    ("lab_technician", "Lab Technician"),
    ("radiologist", "Radiologist"),
    ("dentist", "Dentist"),
    ("other", "Other"),
]

REGISTRATION_STATUS_CHOICES = [
    ("active", "Active"),
    ("suspended", "Suspended"),
    ("revoked", "Revoked"),
    ("expired", "Expired"),
]

CREDENTIAL_TYPE_CHOICES = [
    ("medical_license", "Medical License"),
    ("specialty_board", "Specialty Board"),
    ("cme", "CME"),
    ("bls", "BLS"),
    ("acls", "ACLS"),
    ("other", "Other"),
]

FACILITY_TYPE_CHOICES = [
    ("hospital", "Hospital"),
    ("clinic", "Clinic"),
    ("pharmacy", "Pharmacy"),
    ("laboratory", "Laboratory"),
    ("imaging", "Imaging"),
    ("rehabilitation", "Rehabilitation"),
    ("mental_health", "Mental Health"),
    ("emergency", "Emergency"),
    ("other", "Other"),
]

LICENSE_STATUS_CHOICES = [
    ("active", "Active"),
    ("suspended", "Suspended"),
    ("revoked", "Revoked"),
    ("expired", "Expired"),
]


class PopulationGroup(BaseModel):
    class Meta:
        app_label = "cymed_ph_public_health"
        db_table = "cymed_ph_pop_groups"

    name = models.CharField(max_length=200)
    group_type = models.CharField(max_length=30, choices=GROUP_TYPE_CHOICES)
    description = models.TextField(blank=True)
    # Structured JSON criteria defining group membership rules
    criteria = models.JSONField(default=dict)
    estimated_size = models.PositiveIntegerField(default=0)
    geographic_scope = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.group_type})"


class PopulationSegment(BaseModel):
    class Meta:
        app_label = "cymed_ph_public_health"
        db_table = "cymed_ph_pop_segments"

    population_group = models.ForeignKey(
        PopulationGroup,
        on_delete=models.CASCADE,
        related_name="segments",
    )
    segment_name = models.CharField(max_length=200)
    segment_criteria = models.JSONField(default=dict)
    patient_count = models.PositiveIntegerField(default=0)
    last_calculated_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.segment_name} in {self.population_group_id}"


class HealthRisk(BaseModel):
    class Meta:
        app_label = "cymed_ph_public_health"
        db_table = "cymed_ph_pop_health_risks"
        ordering = ["-assessment_date"]

    patient_id = models.UUIDField(db_index=True)
    risk_type = models.CharField(max_length=30, choices=RISK_TYPE_CHOICES)
    risk_level = models.CharField(max_length=15, choices=RISK_LEVEL_CHOICES, default="low")
    # Score 0-100; may be AI-generated
    risk_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    # ICD-11 codes for relevant conditions -- sourced from TerminologyService
    icd11_codes = models.JSONField(default=list)
    assessment_date = models.DateField()
    next_assessment_date = models.DateField(null=True, blank=True)
    assessed_by_user_id = models.UUIDField(null=True, blank=True)
    is_ai_generated = models.BooleanField(default=False)

    def __str__(self):
        return f"Risk {self.risk_type}/{self.risk_level} for {self.patient_id}"


class HealthGoal(BaseModel):
    class Meta:
        app_label = "cymed_ph_public_health"
        db_table = "cymed_ph_pop_health_goals"

    patient_id = models.UUIDField(db_index=True)
    goal_type = models.CharField(max_length=30, choices=GOAL_TYPE_CHOICES)
    target_value = models.CharField(max_length=100, blank=True)
    current_value = models.CharField(max_length=100, blank=True)
    unit = models.CharField(max_length=30, blank=True)
    start_date = models.DateField()
    target_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=GOAL_STATUS_CHOICES, default="active")
    assigned_provider_id = models.UUIDField(null=True, blank=True)

    def __str__(self):
        return f"Goal {self.goal_type} for {self.patient_id}"


class PopulationProgram(BaseModel):
    class Meta:
        app_label = "cymed_ph_public_health"
        db_table = "cymed_ph_pop_programs"

    name = models.CharField(max_length=200)
    program_type = models.CharField(max_length=30, choices=PROGRAM_TYPE_CHOICES)
    description = models.TextField(blank=True)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    target_population_description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=PROGRAM_STATUS_CHOICES, default="planning")
    program_manager_id = models.UUIDField(null=True, blank=True)
    target_count = models.PositiveIntegerField(default=0)
    enrolled_count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.name} ({self.program_type})"


class NationalProvider(BaseModel):
    class Meta:
        app_label = "cymed_ph_public_health"
        db_table = "cymed_ph_pop_national_providers"

    # Reference to provider in clinical service -- no cross-service FK
    provider_id = models.UUIDField(db_index=True)
    national_provider_number = models.CharField(max_length=100, unique=True)
    provider_type = models.CharField(max_length=30, choices=PROVIDER_TYPE_CHOICES)
    specialty = models.CharField(max_length=100, blank=True)
    registration_date = models.DateField()
    registration_status = models.CharField(
        max_length=20, choices=REGISTRATION_STATUS_CHOICES, default="active"
    )
    primary_facility_id = models.UUIDField(null=True, blank=True)

    def __str__(self):
        return f"{self.national_provider_number} ({self.provider_type})"


class ProviderCredential(BaseModel):
    class Meta:
        app_label = "cymed_ph_public_health"
        db_table = "cymed_ph_pop_provider_credentials"

    national_provider = models.ForeignKey(
        NationalProvider,
        on_delete=models.CASCADE,
        related_name="credentials",
    )
    credential_type = models.CharField(max_length=50, choices=CREDENTIAL_TYPE_CHOICES)
    credential_number = models.CharField(max_length=100)
    issuing_authority = models.CharField(max_length=200)
    issue_date = models.DateField()
    expiry_date = models.DateField(null=True, blank=True)
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.credential_type} -- {self.credential_number}"


class NationalFacility(BaseModel):
    class Meta:
        app_label = "cymed_ph_public_health"
        db_table = "cymed_ph_pop_national_facilities"

    # Reference to facility in clinical service -- no cross-service FK
    facility_id = models.UUIDField(db_index=True)
    national_facility_number = models.CharField(max_length=100, unique=True)
    facility_type = models.CharField(max_length=30, choices=FACILITY_TYPE_CHOICES)
    facility_name = models.CharField(max_length=200)
    license_status = models.CharField(
        max_length=20, choices=LICENSE_STATUS_CHOICES, default="active"
    )
    registration_date = models.DateField()
    beds_count = models.PositiveIntegerField(null=True, blank=True)
    is_teaching = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.facility_name} ({self.national_facility_number})"


class FacilityAccreditation(BaseModel):
    class Meta:
        app_label = "cymed_ph_public_health"
        db_table = "cymed_ph_pop_facility_accreditations"

    national_facility = models.ForeignKey(
        NationalFacility,
        on_delete=models.CASCADE,
        related_name="accreditations",
    )
    # e.g. JCI, CBAHI, ISO
    accreditation_body = models.CharField(max_length=200)
    accreditation_type = models.CharField(max_length=100)
    award_date = models.DateField()
    expiry_date = models.DateField(null=True, blank=True)
    accreditation_level = models.CharField(max_length=50, blank=True)
    is_current = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.accreditation_body} -- {self.accreditation_type}"