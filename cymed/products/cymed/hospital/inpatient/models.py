from django.db import models

from platform.common.fields import EncryptedText
from platform.common.models import BaseModel
from products.cymed.hospital.adt.models import Admission

# Clinical narrative = PHI, encrypted per-tenant at rest (no blind index).


class HospitalStay(BaseModel):
    admission = models.OneToOneField(Admission, on_delete=models.CASCADE, related_name="stay")
    care_team_leader_id = models.UUIDField()
    expected_length_of_stay = models.PositiveIntegerField(default=3)
    actual_length_of_stay = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        db_table = "cymed_hospital_stays"


class DailyRound(BaseModel):
    stay = models.ForeignKey(HospitalStay, on_delete=models.CASCADE, related_name="rounds")
    clinician_id = models.UUIDField()
    round_time = models.DateTimeField(auto_now_add=True)
    subjective_notes = EncryptedText(classification="phi")
    objective_notes = EncryptedText(classification="phi")
    assessment_notes = EncryptedText(classification="phi")
    plan_notes = EncryptedText(classification="phi")

    class Meta:
        db_table = "cymed_hospital_daily_rounds"


class ProgressReview(BaseModel):
    stay = models.ForeignKey(HospitalStay, on_delete=models.CASCADE)
    reviewed_at = models.DateTimeField(auto_now_add=True)
    reviewer_id = models.UUIDField()
    progress_status = models.CharField(max_length=50)  # improving, stable, deteriorating

    class Meta:
        db_table = "cymed_hospital_progress_reviews"


class InpatientCarePlan(BaseModel):
    stay = models.ForeignKey(HospitalStay, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    goals = EncryptedText(classification="phi")
    interventions = EncryptedText(classification="phi")

    class Meta:
        db_table = "cymed_hospital_inpatient_careplans"


class DischargePlanning(BaseModel):
    stay = models.OneToOneField(
        HospitalStay, on_delete=models.CASCADE, related_name="discharge_plan"
    )
    target_discharge_date = models.DateField()
    barriers_to_discharge = EncryptedText(classification="phi")
    is_cleared = models.BooleanField(default=False)

    class Meta:
        db_table = "cymed_hospital_discharge_planning"
