from django.db import models
from platform.common.models import BaseModel


ROLE_TYPE_CHOICES = [
    # Physician grades
    ("intern", "Intern"),
    ("resident", "Resident"),
    ("chief_resident", "Chief Resident"),
    ("fellow", "Fellow"),
    ("specialist", "Specialist"),
    ("consultant", "Consultant"),
    ("attending", "Attending"),
    ("surgeon", "Surgeon"),
    ("emergency_physician", "Emergency Physician"),
    ("hospitalist", "Hospitalist"),
    ("department_chair", "Department Chair"),
    ("medical_director", "Medical Director"),
    # Nursing grades
    ("nurse_manager", "Nurse Manager"),
    ("head_nurse", "Head Nurse"),
    ("charge_nurse", "Charge Nurse"),
    ("staff_nurse", "Staff Nurse"),
    ("senior_nurse", "Senior Nurse"),
    ("icu_nurse", "ICU Nurse"),
    ("er_nurse", "ER Nurse"),
    ("or_nurse", "OR Nurse"),
    ("dialysis_nurse", "Dialysis Nurse"),
    ("ld_nurse", "Labor & Delivery Nurse"),
    ("pediatric_nurse", "Pediatric Nurse"),
    ("nicu_nurse", "NICU Nurse"),
    ("float_nurse", "Float Nurse"),
    ("travel_nurse", "Travel Nurse"),
    ("agency_nurse", "Agency Nurse"),
    # Allied health
    ("pharmacist", "Pharmacist"),
    ("clinical_pharmacist", "Clinical Pharmacist"),
    ("lab_technologist", "Lab Technologist"),
    ("radiologic_technologist", "Radiologic Technologist"),
    ("respiratory_therapist", "Respiratory Therapist"),
    ("physical_therapist", "Physical Therapist"),
    ("occupational_therapist", "Occupational Therapist"),
    ("dialysis_technician", "Dialysis Technician"),
    ("biomedical_engineer", "Biomedical Engineer"),
    ("cssd_technician", "CSSD Technician"),
    ("blood_bank_technologist", "Blood Bank Technologist"),
    ("ward_clerk", "Ward Clerk"),
    ("scheduler", "Scheduler"),
    ("other", "Other"),
]

CONTRACT_TYPE_CHOICES = [
    ("full_time", "Full Time"),
    ("part_time", "Part Time"),
    ("resident_training", "Resident Training"),
    ("fellow_training", "Fellow Training"),
    ("travel", "Travel"),
    ("agency", "Agency"),
    ("locum", "Locum Tenens"),
    ("volunteer", "Volunteer"),
]

CLINICAL_CATEGORY_CHOICES = [
    ("physician", "Physician"),
    ("nursing", "Nursing"),
    ("allied_health", "Allied Health"),
    ("administrative", "Administrative"),
]

CREDENTIAL_TYPE_CHOICES = [
    ("medical_license", "Medical License"),
    ("nursing_license", "Nursing License"),
    ("board_certification", "Board Certification"),
    ("bls", "BLS"),
    ("acls", "ACLS"),
    ("pals", "PALS"),
    ("tncc", "TNCC"),
    ("specialty_certification", "Specialty Certification"),
    ("pacs_admin", "PACS Administrator"),
    ("blood_bank_cert", "Blood Bank Certification"),
    ("scrub_cert", "Scrub/Circulating Certification"),
    ("other", "Other"),
]

CREDENTIAL_STATUS_CHOICES = [
    ("valid", "Valid"),
    ("expiring_soon", "Expiring Soon"),
    ("expired", "Expired"),
    ("revoked", "Revoked"),
    ("pending_renewal", "Pending Renewal"),
]


class WorkforceProfile(BaseModel):
    class Meta:
        app_label = "cymed_hwm_profiles"
        db_table = "cymed_hwm_profiles_profile"
        unique_together = [["tenant_id", "employee_id"]]

    # Sourced from CyCom HR via event sync — no direct DB join
    employee_id = models.UUIDField(db_index=True)
    facility_id = models.UUIDField(db_index=True)
    department_id = models.UUIDField(db_index=True, null=True, blank=True)

    display_name = models.CharField(max_length=200)
    role_type = models.CharField(max_length=40, choices=ROLE_TYPE_CHOICES)
    clinical_category = models.CharField(max_length=30, choices=CLINICAL_CATEGORY_CHOICES)
    contract_type = models.CharField(max_length=30, choices=CONTRACT_TYPE_CHOICES, default="full_time")
    specialty = models.CharField(max_length=100, blank=True)
    sub_specialty = models.CharField(max_length=100, blank=True)

    is_active = models.BooleanField(default=True)
    is_float_eligible = models.BooleanField(default=False)
    can_self_schedule = models.BooleanField(default=True)

    # Cached from CyIdentity SCIM sync
    identity_user_id = models.UUIDField(null=True, blank=True, db_index=True)

    def __str__(self):
        return f"{self.display_name} ({self.role_type})"


class ClinicalCredential(BaseModel):
    class Meta:
        app_label = "cymed_hwm_profiles"
        db_table = "cymed_hwm_profiles_credential"

    profile = models.ForeignKey(
        WorkforceProfile,
        on_delete=models.CASCADE,
        related_name="credentials",
    )
    credential_type = models.CharField(max_length=40, choices=CREDENTIAL_TYPE_CHOICES)
    issuing_body = models.CharField(max_length=200, blank=True)
    credential_number = models.CharField(max_length=100, blank=True)
    issued_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=CREDENTIAL_STATUS_CHOICES, default="valid")
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.credential_type} — {self.profile.display_name}"


class CompetencyRecord(BaseModel):
    class Meta:
        app_label = "cymed_hwm_profiles"
        db_table = "cymed_hwm_profiles_competency"
        unique_together = [["tenant_id", "profile", "competency_code"]]

    profile = models.ForeignKey(
        WorkforceProfile,
        on_delete=models.CASCADE,
        related_name="competencies",
    )
    competency_code = models.CharField(max_length=100)
    competency_name = models.CharField(max_length=200)
    certified_at = models.DateField()
    expiry_date = models.DateField(null=True, blank=True)
    assessed_by_id = models.UUIDField(null=True, blank=True)
    is_current = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.competency_code} — {self.profile.display_name}"
