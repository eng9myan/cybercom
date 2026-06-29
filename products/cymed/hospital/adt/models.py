from django.db import models

from platform.common.models import BaseModel
from products.cymed.core.encounters.models import Encounter
from products.cymed.core.patients.models import Patient


class AdmissionReason(BaseModel):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=100, unique=True)

    class Meta:
        db_table = "cymed_hospital_admission_reasons"

    def __str__(self) -> str:
        return self.name


class AdmissionType(BaseModel):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=100, unique=True)

    class Meta:
        db_table = "cymed_hospital_admission_types"

    def __str__(self) -> str:
        return self.name


class DischargeReason(BaseModel):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=100, unique=True)

    class Meta:
        db_table = "cymed_hospital_discharge_reasons"


class DischargeDisposition(BaseModel):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=100, unique=True)

    class Meta:
        db_table = "cymed_hospital_discharge_dispositions"


class Admission(BaseModel):
    encounter = models.OneToOneField(
        Encounter, on_delete=models.CASCADE, related_name="hospital_admission"
    )
    admission_type = models.ForeignKey(AdmissionType, on_delete=models.PROTECT)
    admission_reason = models.ForeignKey(AdmissionReason, on_delete=models.PROTECT)
    admitting_physician_id = models.UUIDField()
    admitted_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=50,
        choices=[("admitted", "Admitted"), ("discharged", "Discharged")],
        default="admitted",
    )

    class Meta:
        db_table = "cymed_hospital_admissions"


class TransferRequest(BaseModel):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    encounter = models.ForeignKey(Encounter, on_delete=models.CASCADE)
    source_bed_id = models.UUIDField(null=True, blank=True)
    target_bed_id = models.UUIDField()
    requested_by = models.UUIDField()
    requested_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=50,
        choices=[("pending", "Pending"), ("approved", "Approved"), ("rejected", "Rejected")],
        default="pending",
    )
    reason = models.TextField()

    class Meta:
        db_table = "cymed_hospital_transfer_requests"


class TransferApproval(BaseModel):
    transfer_request = models.OneToOneField(
        TransferRequest, on_delete=models.CASCADE, related_name="approval"
    )
    approved_by = models.UUIDField()
    approved_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "cymed_hospital_transfer_approvals"


class DischargeSummary(BaseModel):
    admission = models.OneToOneField(
        Admission, on_delete=models.CASCADE, related_name="discharge_details"
    )
    discharged_at = models.DateTimeField(auto_now_add=True)
    discharged_by = models.UUIDField()
    disposition = models.ForeignKey(DischargeDisposition, on_delete=models.PROTECT)
    reason = models.ForeignKey(DischargeReason, on_delete=models.PROTECT)
    summary_text = models.TextField()
    instructions = models.TextField()

    class Meta:
        db_table = "cymed_hospital_discharge_summaries"
