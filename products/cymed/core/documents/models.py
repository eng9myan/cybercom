from django.db import models
from platform.common.models import BaseModel
from products.cymed.core.patients.models import Patient
from products.cymed.core.encounters.models import Encounter

class DocumentType(models.TextChoices):
    SOAP = "soap", "SOAP Note"
    PROGRESS = "progress", "Progress Note"
    PROCEDURE = "procedure", "Procedure Note"
    CONSULTATION = "consultation", "Consultation Note"
    DISCHARGE = "discharge", "Discharge Summary"

class DocumentStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    FINAL = "final", "Final / Signed"
    AMENDED = "amended", "Amended"

class ClinicalDocument(BaseModel):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="documents")
    encounter = models.ForeignKey(Encounter, on_delete=models.SET_NULL, null=True, blank=True, related_name="documents")
    title = models.CharField(max_length=255)
    document_type = models.CharField(max_length=30, choices=DocumentType.choices)
    status = models.CharField(max_length=20, choices=DocumentStatus.choices, default=DocumentStatus.DRAFT)
    content = models.TextField(blank=True)
    version = models.PositiveIntegerField(default=1)
    parent_document = models.ForeignKey("self", on_delete=models.SET_NULL, null=True, blank=True, related_name="amendments")
    digitally_signed_by = models.CharField(max_length=255, blank=True)
    signed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "cymed_clinical_documents"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.title} (v{self.version})"


class DocumentSection(BaseModel):
    document = models.ForeignKey(ClinicalDocument, on_delete=models.CASCADE, related_name="sections")
    title = models.CharField(max_length=255)
    content = models.TextField()

    class Meta:
        db_table = "cymed_document_sections"


class SOAPNote(BaseModel):
    clinical_document = models.OneToOneField(ClinicalDocument, on_delete=models.CASCADE, related_name="soap_note")
    subjective = models.TextField(blank=True)
    objective = models.TextField(blank=True)
    assessment = models.TextField(blank=True)
    plan = models.TextField(blank=True)

    class Meta:
        db_table = "cymed_soap_notes"


class ProgressNote(BaseModel):
    clinical_document = models.OneToOneField(ClinicalDocument, on_delete=models.CASCADE, related_name="progress_note")
    narrative = models.TextField()

    class Meta:
        db_table = "cymed_progress_notes"


class ProcedureNote(BaseModel):
    clinical_document = models.OneToOneField(ClinicalDocument, on_delete=models.CASCADE, related_name="procedure_note")
    procedure_name = models.CharField(max_length=255)
    description = models.TextField()

    class Meta:
        db_table = "cymed_procedure_notes"


class ConsultationNote(BaseModel):
    clinical_document = models.OneToOneField(ClinicalDocument, on_delete=models.CASCADE, related_name="consultation_note")
    reason_for_consult = models.TextField()
    recommendations = models.TextField()

    class Meta:
        db_table = "cymed_consultation_notes"


class DischargeNote(BaseModel):
    clinical_document = models.OneToOneField(ClinicalDocument, on_delete=models.CASCADE, related_name="discharge_note")
    discharge_status = models.CharField(max_length=100)
    instructions = models.TextField()

    class Meta:
        db_table = "cymed_discharge_notes"
