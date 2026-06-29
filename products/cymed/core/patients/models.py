from django.db import models
from django.utils import timezone

from platform.common.models import BaseModel, SoftDeleteMixin


class GenderType(models.TextChoices):
    MALE = "male", "Male"
    FEMALE = "female", "Female"
    OTHER = "other", "Other"
    UNKNOWN = "unknown", "Unknown"


class Patient(BaseModel, SoftDeleteMixin):
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    dob = models.DateField()
    gender = models.CharField(max_length=10, choices=GenderType.choices, default=GenderType.UNKNOWN)
    mrn = models.CharField(max_length=100, unique=True, db_index=True)
    national_id = models.CharField(max_length=100, null=True, blank=True, unique=True)
    passport_number = models.CharField(max_length=100, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    merged_into = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True, related_name="merged_patients"
    )

    class Meta:
        db_table = "cymed_patients"
        ordering = ["last_name", "first_name"]

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name} ({self.mrn})"


class PatientIdentifier(BaseModel):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="identifiers")
    system = models.CharField(max_length=255)  # e.g., "national-id", "passport"
    value = models.CharField(max_length=255)
    use = models.CharField(
        max_length=30,
        choices=[("official", "Official"), ("secondary", "Secondary"), ("temp", "Temporary")],
        default="official",
    )

    class Meta:
        db_table = "cymed_patient_identifiers"
        unique_together = [("patient", "system", "value")]


class PatientContact(BaseModel):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="contacts")
    telecom_system = models.CharField(
        max_length=20,
        choices=[
            ("phone", "Phone"),
            ("fax", "Fax"),
            ("email", "Email"),
            ("pager", "Pager"),
            ("url", "URL"),
            ("sms", "SMS"),
        ],
    )
    telecom_value = models.CharField(max_length=255)
    use = models.CharField(
        max_length=20,
        choices=[("home", "Home"), ("work", "Work"), ("mobile", "Mobile"), ("old", "Old")],
        default="home",
    )

    class Meta:
        db_table = "cymed_patient_contacts"


class PatientAddress(BaseModel):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="addresses")
    line1 = models.CharField(max_length=255)
    line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100)
    use = models.CharField(
        max_length=20,
        choices=[("home", "Home"), ("work", "Work"), ("billing", "Billing"), ("temp", "Temporary")],
        default="home",
    )

    class Meta:
        db_table = "cymed_patient_addresses"


class PatientCommunication(BaseModel):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="communications")
    language_code = models.CharField(max_length=10)  # e.g., "en", "ar"
    preferred = models.BooleanField(default=False)

    class Meta:
        db_table = "cymed_patient_communications"
        unique_together = [("patient", "language_code")]


class PatientEmergencyContact(BaseModel):
    patient = models.ForeignKey(
        Patient, on_delete=models.CASCADE, related_name="emergency_contacts"
    )
    name = models.CharField(max_length=255)
    relationship_code = models.CharField(max_length=100)  # e.g., "spouse", "parent"
    phone = models.CharField(max_length=50)
    email = models.EmailField(blank=True)

    class Meta:
        db_table = "cymed_patient_emergency_contacts"


class PatientRelationship(BaseModel):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="relationships")
    related_person_name = models.CharField(max_length=255)
    relationship_type = models.CharField(max_length=100)  # e.g., "relative", "guardian"
    telecom = models.CharField(max_length=255, blank=True)
    address = models.TextField(blank=True)

    class Meta:
        db_table = "cymed_patient_relationships"


class PatientConsentReference(BaseModel):
    patient = models.ForeignKey(
        Patient, on_delete=models.CASCADE, related_name="consent_references"
    )
    consent_id = models.UUIDField()

    class Meta:
        db_table = "cymed_patient_consent_references"


class PatientMergeHistory(BaseModel):
    merged_patient = models.ForeignKey(
        Patient, on_delete=models.CASCADE, related_name="merged_from_history"
    )
    target_patient = models.ForeignKey(
        Patient, on_delete=models.CASCADE, related_name="merged_to_history"
    )
    merged_at = models.DateTimeField(default=timezone.now)
    merged_by = models.CharField(max_length=255)
    unmerged_at = models.DateTimeField(null=True, blank=True)
    unmerged_by = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "cymed_patient_merge_history"


class PatientPhoto(BaseModel):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="photos")
    photo_url = models.URLField(max_length=500)
    is_primary = models.BooleanField(default=False)

    class Meta:
        db_table = "cymed_patient_photos"


class PatientLanguage(BaseModel):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="languages")
    language = models.CharField(max_length=100)  # e.g., "Arabic", "English"

    class Meta:
        db_table = "cymed_patient_languages"


class PatientNationality(BaseModel):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="nationalities")
    country_code = models.CharField(max_length=10)  # e.g., "SA", "JO", "AE"

    class Meta:
        db_table = "cymed_patient_nationalities"
