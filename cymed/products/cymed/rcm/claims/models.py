from django.db import models

from platform.common.models import BaseModel


class Claim(BaseModel):
    CLAIM_TYPE_CHOICES = [
        ("institutional", "Institutional"),
        ("professional", "Professional"),
        ("dental", "Dental"),
        ("pharmacy", "Pharmacy"),
    ]
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("ready", "Ready"),
        ("submitted", "Submitted"),
        ("acknowledged", "Acknowledged"),
        ("pending", "Pending"),
        ("paid", "Paid"),
        ("partial", "Partial"),
        ("denied", "Denied"),
        ("voided", "Voided"),
        ("resubmitted", "Resubmitted"),
    ]

    claim_number = models.CharField(max_length=50, unique=True)
    patient_id = models.UUIDField(db_index=True)
    insurance_member_id = models.UUIDField(db_index=True)
    insurance_plan_id = models.UUIDField(db_index=True)
    encounter_billing_id = models.UUIDField(db_index=True)
    claim_type = models.CharField(max_length=20, choices=CLAIM_TYPE_CHOICES)
    claim_date = models.DateField()
    service_from_date = models.DateField()
    service_to_date = models.DateField()
    facility_id = models.UUIDField(db_index=True)
    rendering_provider_id = models.UUIDField()
    referring_provider_id = models.UUIDField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    total_billed_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_approved_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_paid_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    patient_responsibility = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    icd11_primary_diagnosis = models.CharField(max_length=20, blank=True)
    icd11_secondary_diagnoses = models.JSONField(default=list)
    preauthorization_number = models.CharField(max_length=100, blank=True)
    preauthorization_id = models.UUIDField(null=True, blank=True)
    is_resubmission = models.BooleanField(default=False)
    original_claim_id = models.UUIDField(null=True, blank=True)
    fhir_claim_id = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        app_label = "cymed_rcm_claims"
        db_table = "cymed_rcm_clm_claims"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["tenant_id", "patient_id"]),
            models.Index(fields=["tenant_id", "status"]),
            models.Index(fields=["tenant_id", "claim_date"]),
            models.Index(fields=["tenant_id", "insurance_plan_id"]),
        ]

    def __str__(self):
        return f"Claim({self.claim_number} | {self.status})"


class ClaimLine(BaseModel):
    LINE_STATUS_CHOICES = [
        ("included", "Included"),
        ("excluded", "Excluded"),
        ("denied", "Denied"),
        ("pending", "Pending"),
    ]

    claim = models.ForeignKey(Claim, on_delete=models.CASCADE, related_name="lines")
    line_number = models.PositiveSmallIntegerField()
    service_date = models.DateField()
    service_code = models.CharField(max_length=50)
    service_description = models.CharField(max_length=500)
    icd11_diagnosis_code = models.CharField(max_length=20, blank=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    unit_charge = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    line_charge = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    approved_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    line_status = models.CharField(max_length=20, choices=LINE_STATUS_CHOICES, default="included")
    denial_reason_code = models.CharField(max_length=50, blank=True)
    rendering_provider_id = models.UUIDField(null=True, blank=True)
    charge_id = models.UUIDField(null=True, blank=True)

    class Meta:
        app_label = "cymed_rcm_claims"
        db_table = "cymed_rcm_clm_lines"
        ordering = ["line_number"]
        indexes = [models.Index(fields=["tenant_id", "claim_id"])]

    def __str__(self):
        return f"ClaimLine({self.claim_id} | line={self.line_number})"


class ClaimSubmission(BaseModel):
    SUBMISSION_METHOD_CHOICES = [
        ("electronic", "Electronic"),
        ("batch", "Batch"),
        ("portal", "Portal"),
        ("direct", "Direct"),
    ]

    claim = models.ForeignKey(Claim, on_delete=models.CASCADE, related_name="submissions")
    submitted_at = models.DateTimeField(auto_now_add=True)
    submitted_by_user_id = models.UUIDField()
    submission_method = models.CharField(
        max_length=20, choices=SUBMISSION_METHOD_CHOICES, default="electronic"
    )
    payer_transaction_id = models.CharField(max_length=200, blank=True, null=True)
    batch_id = models.CharField(max_length=200, blank=True, null=True)
    acknowledgement_received = models.BooleanField(default=False)
    acknowledgement_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        app_label = "cymed_rcm_claims"
        db_table = "cymed_rcm_clm_submissions"
        ordering = ["-submitted_at"]
        indexes = [models.Index(fields=["tenant_id", "claim_id"])]

    def __str__(self):
        return f"ClaimSubmission({self.claim_id} | {self.submitted_at})"


class ClaimResponse(BaseModel):
    RESPONSE_TYPE_CHOICES = [
        ("acknowledgement", "Acknowledgement"),
        ("payment", "Payment"),
        ("denial", "Denial"),
        ("additional_info_request", "Additional Info Request"),
        ("partial_payment", "Partial Payment"),
    ]
    PAYMENT_METHOD_CHOICES = [
        ("eft", "EFT"),
        ("cheque", "Cheque"),
        ("credit", "Credit"),
        ("other", "Other"),
    ]

    claim = models.ForeignKey(Claim, on_delete=models.CASCADE, related_name="responses")
    response_date = models.DateTimeField()
    response_type = models.CharField(max_length=30, choices=RESPONSE_TYPE_CHOICES)
    payer_claim_number = models.CharField(max_length=200, blank=True)
    approved_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    paid_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    payment_date = models.DateField(null=True, blank=True)
    payment_method = models.CharField(max_length=30, blank=True, choices=PAYMENT_METHOD_CHOICES)
    eob_number = models.CharField(max_length=200, blank=True)
    denial_codes = models.JSONField(default=list)
    remarks = models.TextField(blank=True)
    raw_response = models.JSONField(default=dict)
    fhir_claim_response_id = models.CharField(max_length=200, blank=True, null=True)
    fhir_eob_id = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        app_label = "cymed_rcm_claims"
        db_table = "cymed_rcm_clm_responses"
        ordering = ["-response_date"]
        indexes = [models.Index(fields=["tenant_id", "claim_id"])]

    def __str__(self):
        return f"ClaimResponse({self.claim_id} | {self.response_type})"


class ClaimStatus(BaseModel):
    claim = models.ForeignKey(Claim, on_delete=models.CASCADE, related_name="status_history")
    previous_status = models.CharField(max_length=20)
    new_status = models.CharField(max_length=20)
    changed_at = models.DateTimeField(auto_now_add=True)
    changed_by_user_id = models.UUIDField(null=True, blank=True)
    notes = models.CharField(max_length=500, blank=True)

    class Meta:
        app_label = "cymed_rcm_claims"
        db_table = "cymed_rcm_clm_status_history"
        ordering = ["-changed_at"]
        indexes = [models.Index(fields=["tenant_id", "claim_id"])]

    def __str__(self):
        return f"ClaimStatus({self.claim_id} | {self.previous_status}->{self.new_status})"


class ClaimAttachment(BaseModel):
    ATTACHMENT_TYPE_CHOICES = [
        ("medical_record", "Medical Record"),
        ("lab_result", "Lab Result"),
        ("imaging", "Imaging"),
        ("authorization", "Authorization"),
        ("referral", "Referral"),
        ("notes", "Notes"),
        ("invoice", "Invoice"),
        ("other", "Other"),
    ]

    claim = models.ForeignKey(Claim, on_delete=models.CASCADE, related_name="attachments")
    attachment_type = models.CharField(max_length=30, choices=ATTACHMENT_TYPE_CHOICES)
    file_url = models.CharField(max_length=500)
    file_name = models.CharField(max_length=200)
    uploaded_by_user_id = models.UUIDField()
    is_required = models.BooleanField(default=False)

    class Meta:
        app_label = "cymed_rcm_claims"
        db_table = "cymed_rcm_clm_attachments"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["tenant_id", "claim_id"])]

    def __str__(self):
        return f"ClaimAttachment({self.claim_id} | {self.attachment_type})"
