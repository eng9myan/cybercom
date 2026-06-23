import uuid
from django.db import models
from platform.common.models import BaseModel


class ListType(models.TextChoices):
    MY_PATIENTS = "my_patients", "My Patients"
    WARD = "ward", "Ward"
    CLINIC = "clinic", "Clinic"
    EMERGENCY = "emergency", "Emergency"
    ICU = "icu", "ICU"
    SHARED_TEAM = "shared_team", "Shared Team"
    CUSTOM = "custom", "Custom"


class SortOrder(models.TextChoices):
    NAME = "name", "Name"
    BED_NUMBER = "bed_number", "Bed Number"
    ADMISSION_DATE = "admission_date", "Admission Date"
    ACUITY = "acuity", "Acuity"


class ProviderRole(models.TextChoices):
    ATTENDING = "attending", "Attending"
    COVERING = "covering", "Covering"
    CONSULTING = "consulting", "Consulting"
    PRIMARY_NURSE = "primary_nurse", "Primary Nurse"
    CHARGE_NURSE = "charge_nurse", "Charge Nurse"
    RESIDENT = "resident", "Resident"
    INTERN = "intern", "Intern"
    CO_ATTENDING = "co_attending", "Co-Attending"


class CoverageType(models.TextChoices):
    SCHEDULED = "scheduled", "Scheduled"
    ON_CALL = "on_call", "On Call"
    CROSS_COVER = "cross_cover", "Cross Cover"


class PatientList(BaseModel):
    name = models.CharField(max_length=255)
    list_type = models.CharField(max_length=30, choices=ListType.choices)
    workspace_id = models.UUIDField(db_index=True)
    unit_id = models.UUIDField(null=True, blank=True)
    specialty = models.CharField(max_length=255, blank=True)
    is_shared = models.BooleanField(default=False)
    shared_with = models.JSONField(default=list)
    auto_populate = models.BooleanField(default=True)
    sort_order = models.CharField(max_length=30, choices=SortOrder.choices, default=SortOrder.NAME)
    patient_count = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "cymed_prov_patient_lists"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.list_type})"


class PatientAssignment(BaseModel):
    patient_list = models.ForeignKey(
        PatientList,
        on_delete=models.CASCADE,
        related_name="assignments",
    )
    patient_id = models.UUIDField(db_index=True)
    cymed_encounter_id = models.UUIDField(null=True, blank=True)
    bed_number = models.CharField(max_length=50, blank=True)
    unit_name = models.CharField(max_length=255, blank=True)
    admission_date = models.DateField(null=True, blank=True)
    attending_provider_id = models.UUIDField(null=True, blank=True)
    is_primary = models.BooleanField(default=True)
    acuity_score = models.PositiveSmallIntegerField(null=True, blank=True)
    notes = models.TextField(blank=True)
    added_at = models.DateTimeField(auto_now_add=True)
    removed_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "cymed_prov_patient_assignments"
        unique_together = [("tenant_id", "patient_list", "patient_id")]
        ordering = ["-added_at"]

    def __str__(self):
        return f"Assignment(patient={self.patient_id} list={self.patient_list_id})"


class ProviderAssignment(BaseModel):
    patient_id = models.UUIDField(db_index=True)
    provider_id = models.UUIDField(db_index=True)
    provider_type = models.CharField(max_length=50)
    role = models.CharField(max_length=30, choices=ProviderRole.choices)
    unit_id = models.UUIDField(null=True, blank=True)
    is_primary = models.BooleanField(default=True)
    effective_from = models.DateTimeField()
    effective_until = models.DateTimeField(null=True, blank=True)
    coverage_type = models.CharField(
        max_length=30,
        choices=CoverageType.choices,
        default=CoverageType.SCHEDULED,
    )
    assigned_by = models.UUIDField(null=True, blank=True)

    class Meta:
        db_table = "cymed_prov_provider_assignments"
        ordering = ["-effective_from"]

    def __str__(self):
        return f"ProviderAssignment(patient={self.patient_id} provider={self.provider_id})"


class PatientCensus(BaseModel):
    unit_id = models.UUIDField(db_index=True)
    unit_name = models.CharField(max_length=255)
    census_date = models.DateField(db_index=True)
    total_beds = models.PositiveIntegerField()
    occupied_beds = models.PositiveIntegerField()
    available_beds = models.PositiveIntegerField()
    pending_admissions = models.PositiveIntegerField(default=0)
    pending_discharges = models.PositiveIntegerField(default=0)
    average_acuity = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)
    by_provider = models.JSONField(default=dict)

    class Meta:
        db_table = "cymed_prov_patient_census"
        unique_together = [("tenant_id", "unit_id", "census_date")]
        ordering = ["-census_date"]

    def __str__(self):
        return f"Census({self.unit_name} / {self.census_date})"
