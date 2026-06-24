import uuid
from django.db import models
from platform.common.models import BaseModel


class Preauthorization(BaseModel):
    """
    Represents a pre-authorization request for a clinical service or procedure.
    FHIR: Claim (type=preauthorization) / ClaimResponse
    """

    AUTHORIZATION_TYPE_CHOICES = [
        ("service", "Service"),
        ("procedure", "Procedure"),
        ("medication", "Medication"),
        ("imaging", "Imaging"),
        ("hospitalization", "Hospitalization"),
        ("home_health", "Home Health"),
        ("dme", "Durable Medical Equipment"),
        ("rehabilitation", "Rehabilitation"),
    ]

    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("submitted", "Submitted"),
        ("pending_info", "Pending Information"),
        ("approved", "Approved"),
        ("partially_approved", "Partially Approved"),
        ("denied", "Denied"),
        ("expired", "Expired"),
        ("cancelled", "Cancelled"),
    ]

    PRIORITY_CHOICES = [
        ("routine", "Routine"),
        ("urgent", "Urgent"),
        ("stat", "STAT"),
    ]

    # FHIR: Claim.patient
    patient_id = models.UUIDField(db_index=True)
    # Reference to InsuranceMember UUID
    insurance_member_id = models.UUIDField(db_index=True)
    # Reference to InsurancePlan UUID
    insurance_plan_id = models.UUIDField(db_index=True)
    # FHIR: Claim.encounter
    encounter_id = models.UUIDField(null=True, blank=True)
    # Payer-assigned authorization number upon approval
    # FHIR: ClaimResponse.preAuthRef
    auth_number = models.CharField(max_length=100, unique=True, null=True, blank=True)
    # FHIR: Claim.type (subtype of preauth)
    authorization_type = models.CharField(max_length=30, choices=AUTHORIZATION_TYPE_CHOICES)
    # FHIR: Claim.item[].productOrService (text)
    service_description = models.CharField(max_length=500)
    # ICD-11 diagnosis codes as list of strings — sourced via TerminologyService
    # FHIR: Claim.diagnosis[].diagnosisCodeableConcept
    icd11_diagnosis_codes = models.JSONField(default=list)
    # FHIR: Claim.item[].quantity
    requested_units = models.PositiveIntegerField(default=1)
    # FHIR: ClaimResponse.item[].adjudication (approved quantity)
    approved_units = models.PositiveIntegerField(null=True, blank=True)
    # FHIR: Claim.billablePeriod.start
    requested_start_date = models.DateField()
    # FHIR: Claim.billablePeriod.end
    requested_end_date = models.DateField(null=True, blank=True)
    # FHIR: ClaimResponse.preAuthPeriod.start
    approved_start_date = models.DateField(null=True, blank=True)
    # FHIR: ClaimResponse.preAuthPeriod.end
    approved_end_date = models.DateField(null=True, blank=True)
    # FHIR: Claim.status / ClaimResponse.outcome
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    # FHIR: Claim.priority
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default="routine")
    # FHIR: Claim.provider (requesting/ordering clinician or facility)
    requesting_provider_id = models.UUIDField(db_index=True)
    ordering_provider_id = models.UUIDField(null=True, blank=True)
    facility_id = models.UUIDField(null=True, blank=True)
    # Cross-service reference to the originating clinical order
    source_order_id = models.UUIDField(null=True, blank=True)
    # Which CyMed module generated the request
    source_module = models.CharField(max_length=30, blank=True)

    class Meta:
        app_label = "cymed_rcm_preauthorization"
        db_table = "cymed_rcm_preauths"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["tenant_id", "patient_id"]),
            models.Index(fields=["tenant_id", "status"]),
            models.Index(fields=["tenant_id", "authorization_type"]),
            models.Index(fields=["tenant_id", "insurance_plan_id"]),
            models.Index(fields=["tenant_id", "requesting_provider_id"]),
            models.Index(fields=["auth_number"]),
        ]

    def __str__(self):
        return f"Preauthorization({self.authorization_type} | {self.status} | patient={self.patient_id})"


class AuthorizationRequest(BaseModel):
    """
    Tracks each formal submission of a preauthorization to the payer.
    FHIR: Claim (preauthorization) submission record.
    """

    SUBMISSION_METHOD_CHOICES = [
        ("electronic", "Electronic"),
        ("fax", "Fax"),
        ("phone", "Phone"),
        ("portal", "Portal"),
    ]

    # FHIR: Claim (back-reference)
    preauthorization = models.ForeignKey(
        Preauthorization,
        on_delete=models.CASCADE,
        related_name="requests",
    )
    # Automatically set on creation
    request_date = models.DateTimeField(auto_now_add=True)
    # User who submitted this request
    submitted_by_user_id = models.UUIDField()
    # FHIR: Claim.supportingInfo (narrative clinical notes)
    clinical_notes = models.TextField(blank=True)
    # List of CyData file URLs attached as supporting documentation
    supporting_documents = models.JSONField(default=list)
    # Transaction ID returned by the payer at submission
    payer_reference_number = models.CharField(max_length=200, blank=True, null=True)
    submission_method = models.CharField(max_length=20, choices=SUBMISSION_METHOD_CHOICES, default="electronic")

    class Meta:
        app_label = "cymed_rcm_preauthorization"
        db_table = "cymed_rcm_auth_requests"
        ordering = ["-request_date"]
        indexes = [
            models.Index(fields=["tenant_id", "preauthorization_id"]),
        ]

    def __str__(self):
        return f"AuthorizationRequest({self.preauthorization_id} | method={self.submission_method})"


class AuthorizationDecision(BaseModel):
    """
    Records a payer decision on a preauthorization request.
    FHIR: ClaimResponse (preauthorization response).
    """

    DECISION_CHOICES = [
        ("approved", "Approved"),
        ("partially_approved", "Partially Approved"),
        ("denied", "Denied"),
        ("pending_info", "Pending Information"),
        ("referred_to_committee", "Referred to Committee"),
    ]

    # FHIR: ClaimResponse.request (back-reference to Claim)
    preauthorization = models.ForeignKey(
        Preauthorization,
        on_delete=models.CASCADE,
        related_name="decisions",
    )
    # FHIR: ClaimResponse.outcome
    decision = models.CharField(max_length=20, choices=DECISION_CHOICES)
    # FHIR: ClaimResponse.created
    decision_date = models.DateTimeField()
    # Payer reviewer name or ID
    decided_by_payer_user = models.CharField(max_length=200, blank=True)
    # FHIR: ClaimResponse.processNote (approval)
    approval_notes = models.TextField(blank=True)
    # FHIR: ClaimResponse.error.code (denial reason)
    denial_reason_code = models.CharField(max_length=50, blank=True)
    denial_reason_description = models.TextField(blank=True)
    # Any conditions attached to a conditional approval
    conditions = models.TextField(blank=True)
    # FHIR: ClaimResponse.preAuthPeriod.start
    effective_date = models.DateField(null=True, blank=True)
    # FHIR: ClaimResponse.preAuthPeriod.end
    expiry_date = models.DateField(null=True, blank=True)

    class Meta:
        app_label = "cymed_rcm_preauthorization"
        db_table = "cymed_rcm_auth_decisions"
        ordering = ["-decision_date"]
        indexes = [
            models.Index(fields=["tenant_id", "preauthorization_id"]),
            models.Index(fields=["tenant_id", "decision"]),
        ]

    def __str__(self):
        return f"AuthorizationDecision({self.preauthorization_id} | {self.decision})"


class AuthorizationAppeal(BaseModel):
    """
    Records an appeal against a denied or partially approved preauthorization.
    FHIR: Task (appeal) or extended Claim appeal workflow.
    """

    STATUS_CHOICES = [
        ("submitted", "Submitted"),
        ("under_review", "Under Review"),
        ("approved", "Approved"),
        ("denied", "Denied"),
        ("withdrawn", "Withdrawn"),
    ]

    # FHIR: Task.focus (reference to original preauth Claim)
    preauthorization = models.ForeignKey(
        Preauthorization,
        on_delete=models.PROTECT,
        related_name="appeals",
    )
    # Automatically set on creation
    appeal_date = models.DateTimeField(auto_now_add=True)
    submitted_by_user_id = models.UUIDField()
    appeal_reason = models.TextField()
    # List of CyData file URLs for supporting appeal documents
    supporting_documents = models.JSONField(default=list)
    # 1=first-level, 2=second-level, 3=external/independent review
    appeal_level = models.PositiveSmallIntegerField(default=1)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    outcome_date = models.DateTimeField(null=True, blank=True)
    outcome_notes = models.TextField(blank=True)

    class Meta:
        app_label = "cymed_rcm_preauthorization"
        db_table = "cymed_rcm_auth_appeals"
        ordering = ["-appeal_date"]
        indexes = [
            models.Index(fields=["tenant_id", "preauthorization_id"]),
            models.Index(fields=["tenant_id", "status"]),
            models.Index(fields=["tenant_id", "appeal_level"]),
        ]

    def __str__(self):
        return f"AuthorizationAppeal(level={self.appeal_level} | {self.status} | preauth={self.preauthorization_id})"
