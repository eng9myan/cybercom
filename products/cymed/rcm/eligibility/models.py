import uuid
from django.db import models
from platform.common.models import BaseModel


class EligibilityRequest(BaseModel):
    """
    FHIR: CoverageEligibilityRequest
    Represents a request sent to a payer to verify patient insurance eligibility.
    """

    SERVICE_TYPE_CHOICES = [
        ("medical", "Medical"),
        ("pharmacy", "Pharmacy"),
        ("dental", "Dental"),
        ("vision", "Vision"),
        ("mental_health", "Mental Health"),
        ("substance_abuse", "Substance Abuse"),
        ("preventive", "Preventive"),
        ("emergency", "Emergency"),
    ]

    REQUEST_TYPE_CHOICES = [
        ("real_time", "Real-Time"),
        ("batch", "Batch"),
    ]

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("submitted", "Submitted"),
        ("received", "Received"),
        ("error", "Error"),
    ]

    # FHIR: CoverageEligibilityRequest.patient
    patient_id = models.UUIDField(db_index=True)
    # FHIR: CoverageEligibilityRequest.insurance[].coverage (reference to InsurancePlan)
    insurance_plan_id = models.UUIDField(db_index=True)
    # Reference to InsuranceMember
    insurance_member_id = models.UUIDField(null=True, blank=True)
    # FHIR: CoverageEligibilityRequest.servicedDate
    service_date = models.DateField()
    # FHIR: CoverageEligibilityRequest.item[].category
    service_type = models.CharField(max_length=50, choices=SERVICE_TYPE_CHOICES)
    request_type = models.CharField(max_length=20, choices=REQUEST_TYPE_CHOICES)
    # FHIR: CoverageEligibilityRequest.status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    # FHIR resource ID on external FHIR server
    fhir_coverage_eligibility_request_id = models.CharField(max_length=200, blank=True, null=True)
    payer_transaction_id = models.CharField(max_length=200, blank=True, null=True)
    error_message = models.TextField(blank=True, null=True)

    class Meta:
        app_label = "cymed_rcm_eligibility"
        db_table = "cymed_rcm_elig_requests"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["tenant_id", "patient_id"]),
            models.Index(fields=["tenant_id", "status"]),
            models.Index(fields=["tenant_id", "service_date"]),
        ]

    def __str__(self):
        return f"EligibilityRequest({self.patient_id} | {self.service_type} | {self.status})"


class EligibilityResponse(BaseModel):
    """
    FHIR: CoverageEligibilityResponse
    Stores the payer's response to an eligibility request.
    """

    COVERAGE_STATUS_CHOICES = [
        ("active", "Active"),
        ("inactive", "Inactive"),
        ("pending", "Pending"),
        ("unknown", "Unknown"),
    ]

    # FHIR: CoverageEligibilityResponse.request
    eligibility_request = models.OneToOneField(
        EligibilityRequest,
        on_delete=models.CASCADE,
        related_name="response",
    )
    # FHIR: CoverageEligibilityResponse.insurance[].inforce
    is_eligible = models.BooleanField(default=False)
    # FHIR: CoverageEligibilityResponse.insurance[].coverage.status
    coverage_status = models.CharField(max_length=30, choices=COVERAGE_STATUS_CHOICES)
    # FHIR: CoverageEligibilityResponse.insurance[].benefitPeriod.start
    coverage_start_date = models.DateField(null=True, blank=True)
    # FHIR: CoverageEligibilityResponse.insurance[].benefitPeriod.end
    coverage_end_date = models.DateField(null=True, blank=True)
    # FHIR: CoverageEligibilityResponse.insurance[].item[].benefit (type=deductible)
    deductible_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    deductible_met = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    # FHIR: CoverageEligibilityResponse.insurance[].item[].benefit (type=oop)
    out_of_pocket_max = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    out_of_pocket_met = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    # FHIR: CoverageEligibilityResponse.insurance[].item[].benefit (type=copay)
    copay_amount = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    coinsurance_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    patient_responsibility_estimate = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    # Full raw payer response payload
    raw_response = models.JSONField(default=dict)
    fhir_coverage_eligibility_response_id = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        app_label = "cymed_rcm_eligibility"
        db_table = "cymed_rcm_elig_responses"
        ordering = ["-created_at"]

    def __str__(self):
        return f"EligibilityResponse({self.eligibility_request_id} | eligible={self.is_eligible})"


class CoverageVerification(BaseModel):
    """
    Manual or electronic verification of coverage for a patient encounter.
    """

    VERIFICATION_METHOD_CHOICES = [
        ("electronic", "Electronic"),
        ("phone", "Phone"),
        ("portal", "Portal"),
        ("manual", "Manual"),
    ]

    patient_id = models.UUIDField(db_index=True)
    insurance_plan_id = models.UUIDField(db_index=True)
    # FHIR: reference to Encounter
    encounter_id = models.UUIDField(null=True, blank=True)
    verified_by_user_id = models.UUIDField(null=True, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    verification_method = models.CharField(max_length=30, choices=VERIFICATION_METHOD_CHOICES)
    coverage_confirmed = models.BooleanField(default=False)
    notes = models.TextField(blank=True)

    class Meta:
        app_label = "cymed_rcm_eligibility"
        db_table = "cymed_rcm_coverage_verifications"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["tenant_id", "patient_id"]),
            models.Index(fields=["tenant_id", "encounter_id"]),
        ]

    def __str__(self):
        return f"CoverageVerification({self.patient_id} | confirmed={self.coverage_confirmed})"


class BenefitVerification(BaseModel):
    """
    Detailed benefit verification for a specific benefit type within a CoverageVerification.
    """

    BENEFIT_TYPE_CHOICES = [
        ("hospitalization", "Hospitalization"),
        ("outpatient", "Outpatient"),
        ("emergency", "Emergency"),
        ("surgery", "Surgery"),
        ("lab", "Laboratory"),
        ("imaging", "Imaging"),
        ("pharmacy", "Pharmacy"),
        ("specialist", "Specialist"),
        ("preventive", "Preventive"),
        ("mental_health", "Mental Health"),
        ("physical_therapy", "Physical Therapy"),
        ("other", "Other"),
    ]

    NETWORK_STATUS_CHOICES = [
        ("in_network", "In-Network"),
        ("out_of_network", "Out-of-Network"),
        ("unknown", "Unknown"),
    ]

    coverage_verification = models.ForeignKey(
        CoverageVerification,
        on_delete=models.CASCADE,
        related_name="benefit_verifications",
    )
    benefit_type = models.CharField(max_length=50, choices=BENEFIT_TYPE_CHOICES)
    is_covered = models.BooleanField(default=False)
    requires_preauth = models.BooleanField(default=False)
    coverage_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    copay = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    network_status = models.CharField(max_length=20, choices=NETWORK_STATUS_CHOICES)
    benefit_notes = models.TextField(blank=True)

    class Meta:
        app_label = "cymed_rcm_eligibility"
        db_table = "cymed_rcm_benefit_verifications"
        ordering = ["benefit_type"]

    def __str__(self):
        return f"BenefitVerification({self.benefit_type} | covered={self.is_covered})"
