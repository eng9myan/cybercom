from django.db import models
from platform.common.models import BaseModel
from products.cymed.hospital.inpatient.models import HospitalStay

class DischargeChecklist(BaseModel):
    stay = models.ForeignKey(HospitalStay, on_delete=models.CASCADE)
    task_name = models.CharField(max_length=255)  # medication_recon, follow_up_scheduled, billing_cleared
    status = models.CharField(max_length=50, choices=[
        ("pending", "Pending"), ("completed", "Completed")
    ], default="pending")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "cymed_hospital_discharge_checklists"

class DischargeMedication(BaseModel):
    stay = models.ForeignKey(HospitalStay, on_delete=models.CASCADE)
    medication_code = models.CharField(max_length=100)  # validated via Terminology
    reconciliation_action = models.CharField(max_length=100)  # continued, stopped, modified, new
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "cymed_hospital_discharge_medications"

class FollowUpAppointment(BaseModel):
    stay = models.ForeignKey(HospitalStay, on_delete=models.CASCADE)
    specialty_code = models.CharField(max_length=100)
    target_date = models.DateField()
    scheduled_appointment_id = models.UUIDField(null=True, blank=True)

    class Meta:
        db_table = "cymed_hospital_discharge_followups"

class DischargeInstruction(BaseModel):
    stay = models.OneToOneField(HospitalStay, on_delete=models.CASCADE, related_name="instructions")
    dietary_instructions = models.TextField(blank=True)
    activity_restrictions = models.TextField(blank=True)
    warning_symptoms = models.TextField()

    class Meta:
        db_table = "cymed_hospital_discharge_instructions"
