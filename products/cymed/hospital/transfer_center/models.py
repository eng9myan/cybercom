from django.db import models
from platform.common.models import BaseModel
from products.cymed.core.patients.models import Patient

class ReceivingFacility(BaseModel):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=100, unique=True)
    facility_type = models.CharField(max_length=100)  # hospital, rehab, nursing_home

    class Meta:
        db_table = "cymed_hospital_transfer_facilities"

class TransferCase(BaseModel):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    source_hospital_name = models.CharField(max_length=255)
    target_facility = models.ForeignKey(ReceivingFacility, on_delete=models.PROTECT)
    status = models.CharField(max_length=50, choices=[
        ("initiated", "Initiated"),
        ("under_review", "Under Review"),
        ("accepted", "Accepted"),
        ("completed", "Completed"),
        ("rejected", "Rejected")
    ], default="initiated")
    reason = models.TextField()

    class Meta:
        db_table = "cymed_hospital_transfer_cases"

class ExternalReferral(BaseModel):
    transfer_case = models.ForeignKey(TransferCase, on_delete=models.CASCADE)
    referring_physician_name = models.CharField(max_length=255)
    referral_document_url = models.URLField(max_length=500, blank=True)

    class Meta:
        db_table = "cymed_hospital_transfer_referrals"

class AcceptanceReview(BaseModel):
    transfer_case = models.OneToOneField(TransferCase, on_delete=models.CASCADE, related_name="review")
    reviewed_by = models.UUIDField()
    reviewed_at = models.DateTimeField(auto_now_add=True)
    decision = models.CharField(max_length=50, choices=[
        ("accept", "Accept"), ("deny", "Deny")
    ])
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "cymed_hospital_transfer_reviews"
