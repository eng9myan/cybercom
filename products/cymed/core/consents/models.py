from django.db import models
from django.utils import timezone
from platform.common.models import BaseModel
from products.cymed.core.patients.models import Patient

class ConsentCategory(models.TextChoices):
    TREATMENT = "treatment", "Treatment Consent"
    RESEARCH = "research", "Research Consent"
    DATA_SHARING = "data_sharing", "Data Sharing Consent"
    TELEMEDICINE = "telemedicine", "Telemedicine Consent"

class Consent(BaseModel):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="consents")
    category = models.CharField(max_length=30, choices=ConsentCategory.choices)
    status = models.CharField(max_length=30, choices=[
        ("active", "Active"), ("inactive", "Inactive"), ("proposed", "Proposed")
    ], default="active")
    policy_rule = models.TextField()
    start_time = models.DateTimeField(default=timezone.now)
    end_time = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "cymed_consents"
        ordering = ["-start_time"]

    def __str__(self) -> str:
        return f"Consent({self.category}, {self.status}, {self.patient.mrn})"


class ConsentSignature(BaseModel):
    consent = models.OneToOneField(Consent, on_delete=models.CASCADE, related_name="signature")
    signatory_name = models.CharField(max_length=255)
    signature_image_url = models.URLField(max_length=500, blank=True)
    signed_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "cymed_consent_signatures"


class ConsentWitness(BaseModel):
    consent = models.ForeignKey(Consent, on_delete=models.CASCADE, related_name="witnesses")
    witness_name = models.CharField(max_length=255)
    witnessed_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "cymed_consent_witnesses"


class ConsentAudit(BaseModel):
    consent = models.ForeignKey(Consent, on_delete=models.CASCADE, related_name="audits")
    action = models.CharField(max_length=100)  # e.g., "created", "revoked", "printed"
    performed_by = models.CharField(max_length=255)
    performed_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "cymed_consent_audits"
