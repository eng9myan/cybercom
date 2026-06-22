from django.db import models
from django.utils import timezone
from platform.common.models import BaseModel
from products.cymed.core.patients.models import Patient
from products.cymed.core.providers.models import Provider
from products.cymed.core.organizations.models import Organization
from products.cymed.core.facilities.models import Facility, Room, Bed

class EncounterType(models.TextChoices):
    OUTPATIENT = "outpatient", "Outpatient"
    EMERGENCY = "emergency", "Emergency"
    INPATIENT = "inpatient", "Inpatient"
    TELEMEDICINE = "telemedicine", "Telemedicine"
    HOME_CARE = "home_care", "Home Care"

class EncounterStatus(models.TextChoices):
    PLANNED = "planned", "Planned"
    ARRIVED = "arrived", "Arrived"
    IN_PROGRESS = "in_progress", "In Progress"
    FINISHED = "finished", "Finished"
    CANCELLED = "cancelled", "Cancelled"

class EpisodeOfCare(BaseModel):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="episodes_of_care")
    status = models.CharField(max_length=30, choices=[("active", "Active"), ("completed", "Completed"), ("cancelled", "Cancelled")])
    start_time = models.DateTimeField(default=timezone.now)
    end_time = models.DateTimeField(null=True, blank=True)
    managing_organization = models.ForeignKey(Organization, on_delete=models.CASCADE)

    class Meta:
        db_table = "cymed_episodes_of_care"


class Encounter(BaseModel):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="encounters")
    episode_of_care = models.ForeignKey(EpisodeOfCare, on_delete=models.SET_NULL, null=True, blank=True, related_name="encounters")
    encounter_type = models.CharField(max_length=30, choices=EncounterType.choices)
    status = models.CharField(max_length=30, choices=EncounterStatus.choices, default=EncounterStatus.PLANNED)
    start_time = models.DateTimeField(default=timezone.now)
    end_time = models.DateTimeField(null=True, blank=True)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="encounters")
    facility = models.ForeignKey(Facility, on_delete=models.CASCADE, related_name="encounters")

    class Meta:
        db_table = "cymed_encounters"
        ordering = ["-start_time"]

    def __str__(self) -> str:
        return f"Encounter({self.patient.mrn}, {self.encounter_type}, {self.status})"


class EncounterParticipant(BaseModel):
    encounter = models.ForeignKey(Encounter, on_delete=models.CASCADE, related_name="participants")
    provider = models.ForeignKey(Provider, on_delete=models.CASCADE, related_name="encounters")
    role = models.CharField(max_length=50, choices=[
        ("lead", "Lead Attending Physician"),
        ("attending", "Attending Physician"),
        ("consulting", "Consulting Physician"),
        ("referring", "Referring Professional")
    ], default="attending")

    class Meta:
        db_table = "cymed_encounter_participants"


class EncounterReason(BaseModel):
    encounter = models.ForeignKey(Encounter, on_delete=models.CASCADE, related_name="reasons")
    reason_code = models.CharField(max_length=100)  # SNOMED or ICD-11
    reason_text = models.TextField()

    class Meta:
        db_table = "cymed_encounter_reasons"


class EncounterDiagnosis(BaseModel):
    encounter = models.ForeignKey(Encounter, on_delete=models.CASCADE, related_name="diagnoses")
    condition_code = models.CharField(max_length=100)  # ICD-11 or SNOMED
    display = models.CharField(max_length=255)
    use = models.CharField(max_length=50, choices=[
        ("admission", "Admission Diagnosis"),
        ("discharge", "Discharge Diagnosis"),
        ("chief_complaint", "Chief Complaint")
    ], default="chief_complaint")

    class Meta:
        db_table = "cymed_encounter_diagnoses"


class EncounterLocation(BaseModel):
    encounter = models.ForeignKey(Encounter, on_delete=models.CASCADE, related_name="locations")
    room = models.ForeignKey(Room, on_delete=models.SET_NULL, null=True, blank=True)
    bed = models.ForeignKey(Bed, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=30, choices=[("active", "Active"), ("completed", "Completed")])
    start_time = models.DateTimeField(default=timezone.now)
    end_time = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "cymed_encounter_locations"


class EncounterStatusHistory(BaseModel):
    encounter = models.ForeignKey(Encounter, on_delete=models.CASCADE, related_name="status_history")
    status = models.CharField(max_length=30, choices=EncounterStatus.choices)
    changed_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "cymed_encounter_status_history"


class EncounterNote(BaseModel):
    encounter = models.ForeignKey(Encounter, on_delete=models.CASCADE, related_name="notes")
    note_text = models.TextField()
    recorded_by = models.CharField(max_length=255)
    recorded_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "cymed_encounter_notes"
