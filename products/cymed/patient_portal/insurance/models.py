from django.db import models

from platform.common.models import BaseModel


class InsuranceCard(BaseModel):
    PLAN_TYPE_CHOICES = [
        ("individual", "Individual"),
        ("family", "Family"),
        ("corporate", "Corporate"),
        ("government", "Government"),
    ]

    account_id = models.UUIDField(db_index=True)
    patient_id = models.UUIDField(db_index=True)
    insurer_name = models.CharField(max_length=255)
    insurer_name_ar = models.CharField(max_length=255, blank=True)
    policy_number = models.CharField(max_length=100, db_index=True)
    member_id = models.CharField(max_length=100)
    group_number = models.CharField(max_length=100, blank=True)
    plan_name = models.CharField(max_length=255, blank=True)
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPE_CHOICES, default="individual")
    card_front_url = models.URLField(max_length=2000, blank=True)
    card_back_url = models.URLField(max_length=2000, blank=True)
    effective_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    is_primary = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    coverage_details = models.JSONField(default=dict)
    copay_details = models.JSONField(default=dict)
    deductible = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    out_of_pocket_max = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    class Meta:
        db_table = "cymed_portal_insurance_cards"
        indexes = [
            models.Index(fields=["account_id", "is_active", "is_primary"]),
        ]

    def __str__(self):
        return f"{self.insurer_name} - {self.policy_number}"


class CoverageVerification(BaseModel):
    VERIFICATION_TYPE_CHOICES = [
        ("eligibility", "Eligibility"),
        ("benefits", "Benefits"),
        ("specific_service", "Specific Service"),
    ]
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("verified", "Verified"),
        ("not_covered", "Not Covered"),
        ("partially_covered", "Partially Covered"),
        ("failed", "Failed"),
    ]

    account_id = models.UUIDField(db_index=True)
    patient_id = models.UUIDField(db_index=True)
    insurance_card = models.ForeignKey(
        InsuranceCard,
        related_name="verifications",
        on_delete=models.CASCADE,
    )
    verification_type = models.CharField(
        max_length=20, choices=VERIFICATION_TYPE_CHOICES, default="eligibility"
    )
    service_type = models.CharField(max_length=100, blank=True)
    service_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    coverage_percentage = models.PositiveSmallIntegerField(null=True, blank=True)
    patient_responsibility = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    verification_details = models.JSONField(default=dict)
    verified_at = models.DateTimeField(null=True, blank=True)
    valid_until = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "cymed_portal_coverage_verifications"
        indexes = [
            models.Index(fields=["account_id", "status"]),
        ]

    def __str__(self):
        return f"Verification {self.verification_type} - {self.status}"


class PreauthorizationRequest(BaseModel):
    STATUS_CHOICES = [
        ("submitted", "Submitted"),
        ("under_review", "Under Review"),
        ("approved", "Approved"),
        ("denied", "Denied"),
        ("pending_info", "Pending Info"),
        ("expired", "Expired"),
    ]

    account_id = models.UUIDField(db_index=True)
    patient_id = models.UUIDField(db_index=True)
    insurance_card = models.ForeignKey(
        InsuranceCard,
        related_name="preauths",
        on_delete=models.CASCADE,
    )
    service_type = models.CharField(max_length=100)
    service_description = models.TextField()
    provider_name = models.CharField(max_length=255, blank=True)
    provider_id = models.UUIDField(null=True, blank=True)
    service_date = models.DateField(null=True, blank=True)
    diagnosis_codes = models.JSONField(default=list)
    procedure_codes = models.JSONField(default=list)
    estimated_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="submitted")
    auth_number = models.CharField(max_length=100, blank=True)
    approved_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    denial_reason = models.TextField(blank=True)
    valid_from = models.DateField(null=True, blank=True)
    valid_until = models.DateField(null=True, blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "cymed_portal_preauth_requests"
        indexes = [
            models.Index(fields=["account_id", "status"]),
        ]

    def __str__(self):
        return f"Preauth {self.service_type} - {self.status}"


class ClaimStatus(BaseModel):
    STATUS_CHOICES = [
        ("submitted", "Submitted"),
        ("processing", "Processing"),
        ("paid", "Paid"),
        ("denied", "Denied"),
        ("appealing", "Appealing"),
        ("closed", "Closed"),
    ]

    account_id = models.UUIDField(db_index=True)
    patient_id = models.UUIDField(db_index=True)
    insurance_card = models.ForeignKey(
        InsuranceCard,
        related_name="claims",
        on_delete=models.CASCADE,
    )
    claim_number = models.CharField(max_length=100, db_index=True)
    service_date = models.DateField()
    service_type = models.CharField(max_length=100, blank=True)
    provider_name = models.CharField(max_length=255, blank=True)
    billed_amount = models.DecimalField(max_digits=10, decimal_places=2)
    allowed_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    patient_responsibility = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="submitted")
    denial_reason = models.TextField(blank=True)
    eob_url = models.URLField(max_length=2000, blank=True)

    class Meta:
        db_table = "cymed_portal_claims"
        indexes = [
            models.Index(fields=["account_id", "status", "service_date"]),
        ]

    def __str__(self):
        return f"Claim {self.claim_number} - {self.status}"
