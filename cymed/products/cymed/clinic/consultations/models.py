from django.db import models

from platform.common.fields import EncryptedText
from platform.common.models import BaseModel
from products.cymed.core.encounters.models import Encounter

# Clinical narrative is PHI — encrypted per-tenant at rest (no blind index).


class Consultation(BaseModel):
    encounter = models.ForeignKey(
        Encounter, on_delete=models.CASCADE, related_name="clinic_consultations"
    )
    consulted_at = models.DateTimeField(auto_now_add=True)
    consulted_by = models.CharField(max_length=255)
    subjective = EncryptedText(classification="phi")
    objective = EncryptedText(classification="phi")
    assessment = EncryptedText(classification="phi")
    plan = EncryptedText(classification="phi")

    class Meta:
        db_table = "cymed_clinic_consultations"


class ConsultationDiagnosis(BaseModel):
    consultation = models.ForeignKey(
        Consultation, on_delete=models.CASCADE, related_name="diagnoses"
    )
    code = models.CharField(max_length=100)
    system = models.CharField(max_length=50)  # icd11, snomed
    display = EncryptedText(classification="phi")  # diagnosis text
    status = models.CharField(max_length=50, default="confirmed")

    class Meta:
        db_table = "cymed_clinic_consultation_diagnoses"


class ConsultationProcedure(BaseModel):
    consultation = models.ForeignKey(
        Consultation, on_delete=models.CASCADE, related_name="procedures"
    )
    code = models.CharField(max_length=100)
    system = models.CharField(max_length=50)  # snomed, loinc
    display = EncryptedText(classification="phi")  # procedure text
    notes = EncryptedText(classification="phi")

    class Meta:
        db_table = "cymed_clinic_consultation_procedures"


class ConsultationPlan(BaseModel):
    consultation = models.OneToOneField(
        Consultation, on_delete=models.CASCADE, related_name="treatment_plan"
    )
    instructions = EncryptedText(classification="phi")
    prescriptions = models.JSONField(default=list)  # list of drug directives (TODO: EncryptedJSON)

    class Meta:
        db_table = "cymed_clinic_consultation_plans"


class ConsultationFollowUp(BaseModel):
    consultation = models.ForeignKey(
        Consultation, on_delete=models.CASCADE, related_name="follow_ups"
    )
    follow_up_date = models.DateField()
    reason = EncryptedText(classification="phi")

    class Meta:
        db_table = "cymed_clinic_consultation_follow_ups"


class ConsultationAttachment(BaseModel):
    consultation = models.ForeignKey(
        Consultation, on_delete=models.CASCADE, related_name="attachments"
    )
    title = models.CharField(max_length=255)
    file_url = models.URLField(max_length=500)

    class Meta:
        db_table = "cymed_clinic_consultation_attachments"
