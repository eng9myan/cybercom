from django.db import models

from platform.common.models import BaseModel, SoftDeleteMixin


class ProviderType(models.TextChoices):
    PHYSICIAN = "physician", "Physician"
    NURSE = "nurse", "Nurse"
    PHARMACIST = "pharmacist", "Pharmacist"
    RADIOLOGIST = "radiologist", "Radiologist"
    LAB_TECHNICIAN = "lab_technician", "Lab Technician"
    THERAPIST = "therapist", "Therapist"
    ADMINISTRATOR = "administrator", "Administrator"


class Provider(BaseModel, SoftDeleteMixin):
    user_id = models.UUIDField(db_index=True)  # maps to cyidentity UserProfile id
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    provider_type = models.CharField(max_length=30, choices=ProviderType.choices)
    npi = models.CharField(max_length=100, unique=True, db_index=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "cymed_providers"
        ordering = ["last_name", "first_name"]

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name} ({self.provider_type})"


class ProviderIdentifier(BaseModel):
    provider = models.ForeignKey(Provider, on_delete=models.CASCADE, related_name="identifiers")
    system = models.CharField(max_length=255)
    value = models.CharField(max_length=255)

    class Meta:
        db_table = "cymed_provider_identifiers"
        unique_together = [("provider", "system", "value")]


class ProviderLicense(BaseModel):
    provider = models.ForeignKey(Provider, on_delete=models.CASCADE, related_name="licenses")
    license_number = models.CharField(max_length=100)
    state_issued = models.CharField(max_length=100)
    expiry_date = models.DateField()

    class Meta:
        db_table = "cymed_provider_licenses"


class ProviderCredential(BaseModel):
    provider = models.ForeignKey(Provider, on_delete=models.CASCADE, related_name="credentials")
    title = models.CharField(max_length=100)  # MD, RN, etc.
    issuer = models.CharField(max_length=255)
    date_issued = models.DateField()

    class Meta:
        db_table = "cymed_provider_credentials"


class ProviderSpecialty(BaseModel):
    provider = models.ForeignKey(Provider, on_delete=models.CASCADE, related_name="specialties")
    specialty_code = models.CharField(max_length=100)
    specialty_display = models.CharField(max_length=255)

    class Meta:
        db_table = "cymed_provider_specialties"


class ProviderAvailability(BaseModel):
    provider = models.ForeignKey(Provider, on_delete=models.CASCADE, related_name="availability")
    day_of_week = models.PositiveSmallIntegerField()  # 0=Monday, 6=Sunday
    available_start_time = models.TimeField()
    available_end_time = models.TimeField()

    class Meta:
        db_table = "cymed_provider_availability"


class ProviderSchedule(BaseModel):
    provider = models.ForeignKey(Provider, on_delete=models.CASCADE, related_name="schedules")
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_unavailable = models.BooleanField(default=False)

    class Meta:
        db_table = "cymed_provider_schedules"


class ProviderRole(BaseModel):
    provider = models.ForeignKey(Provider, on_delete=models.CASCADE, related_name="roles")
    role_code = models.CharField(max_length=100)  # e.g., "attending", "resident"
    organization_id = models.UUIDField()  # references organization registry

    class Meta:
        db_table = "cymed_provider_roles"


class ProviderEducation(BaseModel):
    provider = models.ForeignKey(Provider, on_delete=models.CASCADE, related_name="education")
    degree = models.CharField(max_length=255)
    school = models.CharField(max_length=255)
    year = models.PositiveIntegerField()

    class Meta:
        db_table = "cymed_provider_education"


class ProviderCertification(BaseModel):
    provider = models.ForeignKey(Provider, on_delete=models.CASCADE, related_name="certifications")
    certification_name = models.CharField(max_length=255)
    expiry_date = models.DateField()

    class Meta:
        db_table = "cymed_provider_certifications"
