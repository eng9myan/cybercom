from django.db import models

from platform.common.models import BaseModel


class InsuranceCompany(BaseModel):
    """
    Represents an insurance company / payer entity.
    FHIR: Organization (with type = 'pay')
    """

    COMPANY_TYPE_CHOICES = [
        ("private", "Private"),
        ("government", "Government"),
        ("semi_government", "Semi-Government"),
        ("cooperative", "Cooperative"),
        ("international", "International"),
    ]

    # FHIR: Organization.name
    name = models.CharField(max_length=200)
    short_name = models.CharField(max_length=50)
    company_type = models.CharField(max_length=20, choices=COMPANY_TYPE_CHOICES)
    # EDI X12 payer ID used for electronic transactions
    payer_id = models.CharField(max_length=50, unique=True)
    # ISO 3166-1 alpha-3 country code
    country = models.CharField(max_length=3, default="SAU")
    is_active = models.BooleanField(default=True)
    # FHIR: Organization.telecom (phone)
    contact_phone = models.CharField(max_length=30, blank=True)
    # FHIR: Organization.telecom (email)
    contact_email = models.EmailField(blank=True)
    portal_url = models.CharField(max_length=500, blank=True)
    # Endpoint for real-time eligibility verification (FHIR or X12 270/271)
    eligibility_endpoint = models.CharField(max_length=500, blank=True)
    # Endpoint for claims submission (FHIR or X12 837)
    claims_endpoint = models.CharField(max_length=500, blank=True)

    class Meta:
        app_label = "cymed_rcm_insurance"
        db_table = "cymed_rcm_ins_companies"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["tenant_id", "is_active"]),
            models.Index(fields=["tenant_id", "company_type"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.payer_id})"


class InsurancePlan(BaseModel):
    """
    Represents a specific insurance plan offered by an InsuranceCompany.
    FHIR: InsurancePlan
    """

    PLAN_TYPE_CHOICES = [
        ("hmo", "HMO"),
        ("ppo", "PPO"),
        ("epo", "EPO"),
        ("pos", "POS"),
        ("indemnity", "Indemnity"),
        ("government", "Government"),
        ("corporate", "Corporate"),
        ("family", "Family"),
        ("individual", "Individual"),
    ]

    NETWORK_TYPE_CHOICES = [
        ("in_network", "In-Network"),
        ("out_of_network", "Out-of-Network"),
        ("both", "Both"),
    ]

    COVERAGE_CATEGORY_CHOICES = [
        ("basic", "Basic"),
        ("standard", "Standard"),
        ("enhanced", "Enhanced"),
        ("premium", "Premium"),
        ("catastrophic", "Catastrophic"),
    ]

    # FHIR: InsurancePlan.ownedBy (reference to Organization)
    company = models.ForeignKey(
        InsuranceCompany,
        on_delete=models.PROTECT,
        related_name="plans",
    )
    # FHIR: InsurancePlan.name
    plan_name = models.CharField(max_length=200)
    plan_code = models.CharField(max_length=50)
    # FHIR: InsurancePlan.type
    plan_type = models.CharField(max_length=30, choices=PLAN_TYPE_CHOICES)
    network_type = models.CharField(max_length=20, choices=NETWORK_TYPE_CHOICES)
    coverage_category = models.CharField(max_length=30, choices=COVERAGE_CATEGORY_CHOICES)
    is_active = models.BooleanField(default=True)
    # FHIR: InsurancePlan.period.start
    effective_date = models.DateField(null=True, blank=True)
    # FHIR: InsurancePlan.period.end
    expiry_date = models.DateField(null=True, blank=True)
    # FHIR: InsurancePlan.coverage[].limit
    max_annual_benefit = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)

    class Meta:
        app_label = "cymed_rcm_insurance"
        db_table = "cymed_rcm_ins_plans"
        ordering = ["company", "plan_name"]
        indexes = [
            models.Index(fields=["tenant_id", "is_active"]),
            models.Index(fields=["tenant_id", "plan_type"]),
        ]

    def __str__(self):
        return f"{self.plan_name} ({self.plan_code}) - {self.company.short_name}"


class InsuranceMember(BaseModel):
    """
    Represents a patient's enrollment in an InsurancePlan.
    FHIR: Coverage
    """

    MEMBER_RELATIONSHIP_CHOICES = [
        ("self", "Self"),
        ("spouse", "Spouse"),
        ("child", "Child"),
        ("dependent", "Dependent"),
        ("other", "Other"),
    ]

    # FHIR: Coverage.beneficiary (reference to Patient)
    patient_id = models.UUIDField(db_index=True)
    # FHIR: Coverage.payor + Coverage.class (plan)
    insurance_plan = models.ForeignKey(
        InsurancePlan,
        on_delete=models.PROTECT,
        related_name="members",
    )
    # FHIR: Coverage.identifier (memberId)
    member_id = models.CharField(max_length=100)
    group_number = models.CharField(max_length=100, blank=True)
    # FHIR: Coverage.relationship
    member_relationship = models.CharField(max_length=20, choices=MEMBER_RELATIONSHIP_CHOICES)
    is_primary_holder = models.BooleanField(default=True)
    # If not self, reference to the primary policyholder patient
    primary_holder_patient_id = models.UUIDField(null=True, blank=True)
    # FHIR: Coverage.period.start
    effective_date = models.DateField()
    # FHIR: Coverage.period.end
    expiry_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    # 1=primary, 2=secondary, 3=tertiary (for COB - Coordination of Benefits)
    priority_order = models.PositiveSmallIntegerField(default=1)

    class Meta:
        app_label = "cymed_rcm_insurance"
        db_table = "cymed_rcm_ins_members"
        ordering = ["patient_id", "priority_order"]
        unique_together = [["tenant_id", "patient_id", "insurance_plan", "priority_order"]]
        indexes = [
            models.Index(fields=["tenant_id", "patient_id"]),
            models.Index(fields=["tenant_id", "is_active"]),
            models.Index(fields=["tenant_id", "priority_order"]),
        ]

    def __str__(self):
        return f"InsuranceMember({self.patient_id} | {self.insurance_plan.plan_code} | priority={self.priority_order})"


class Coverage(BaseModel):
    """
    Represents the coverage details for an InsuranceMember under a specific coverage type.
    FHIR: Coverage (nested coverage details)
    """

    COVERAGE_TYPE_CHOICES = [
        ("medical", "Medical"),
        ("dental", "Dental"),
        ("vision", "Vision"),
        ("pharmacy", "Pharmacy"),
        ("mental_health", "Mental Health"),
        ("maternity", "Maternity"),
        ("rehabilitation", "Rehabilitation"),
        ("other", "Other"),
    ]

    # FHIR: Coverage.identifier (back-reference)
    insurance_member = models.ForeignKey(
        InsuranceMember,
        on_delete=models.PROTECT,
        related_name="coverages",
    )
    # FHIR: Coverage.type
    coverage_type = models.CharField(max_length=30, choices=COVERAGE_TYPE_CHOICES)
    is_active = models.BooleanField(default=True)
    # FHIR: Coverage.period.start
    start_date = models.DateField()
    # FHIR: Coverage.period.end
    end_date = models.DateField(null=True, blank=True)
    # FHIR: Coverage.costToBeneficiary (deductible individual)
    deductible_individual = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    # FHIR: Coverage.costToBeneficiary (deductible family)
    deductible_family = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    # FHIR: Coverage.costToBeneficiary (oop individual)
    out_of_pocket_individual = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    # FHIR: Coverage.costToBeneficiary (oop family)
    out_of_pocket_family = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    # ID of Coverage resource on external FHIR server
    fhir_coverage_id = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        app_label = "cymed_rcm_insurance"
        db_table = "cymed_rcm_ins_coverages"
        ordering = ["insurance_member", "coverage_type"]
        indexes = [
            models.Index(fields=["tenant_id", "coverage_type"]),
            models.Index(fields=["tenant_id", "is_active"]),
        ]

    def __str__(self):
        return (
            f"Coverage({self.insurance_member_id} | {self.coverage_type} | active={self.is_active})"
        )


class Benefit(BaseModel):
    """
    Specific benefit within a Coverage, detailing per-service cost sharing.
    FHIR: Coverage.costToBeneficiary / InsurancePlan.plan.specificCost
    """

    # FHIR: Coverage.costToBeneficiary.type
    coverage = models.ForeignKey(
        Coverage,
        on_delete=models.CASCADE,
        related_name="benefits",
    )
    # e.g. "specialist_visit", "inpatient_stay", "lab_test"
    service_category = models.CharField(max_length=50)
    # FHIR: coverage percentage (100 = fully covered)
    coverage_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=100)
    copay_amount = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    requires_preauth = models.BooleanField(default=False)
    # Maximum annual benefit dollar amount for this service category
    annual_limit = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    # Maximum number of visits/encounters per year
    visit_limit = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        app_label = "cymed_rcm_insurance"
        db_table = "cymed_rcm_ins_benefits"
        ordering = ["coverage", "service_category"]

    def __str__(self):
        return f"Benefit({self.service_category} | {self.coverage_percentage}% | copay={self.copay_amount})"


class CoverageRule(BaseModel):
    """
    Business rules applied at the insurance plan level for coverage determination.
    Examples: pre-auth requirements, network restrictions, exclusions.
    """

    RULE_TYPE_CHOICES = [
        ("preauth_required", "Pre-Authorization Required"),
        ("exclusion", "Exclusion"),
        ("limitation", "Limitation"),
        ("copay_waiver", "Copay Waiver"),
        ("referral_required", "Referral Required"),
        ("network_restriction", "Network Restriction"),
    ]

    insurance_plan = models.ForeignKey(
        InsurancePlan,
        on_delete=models.CASCADE,
        related_name="coverage_rules",
    )
    rule_type = models.CharField(max_length=30, choices=RULE_TYPE_CHOICES)
    # CPT, HCPCS, or ICD code this rule applies to (blank = applies to all)
    service_code = models.CharField(max_length=50, blank=True)
    rule_description = models.TextField()
    is_active = models.BooleanField(default=True)

    class Meta:
        app_label = "cymed_rcm_insurance"
        db_table = "cymed_rcm_ins_coverage_rules"
        ordering = ["insurance_plan", "rule_type"]
        indexes = [
            models.Index(fields=["tenant_id", "rule_type"]),
            models.Index(fields=["tenant_id", "is_active"]),
        ]

    def __str__(self):
        return f"CoverageRule({self.rule_type} | {self.service_code or 'all'})"


class InsuranceCard(BaseModel):
    """
    Stores digital copies (front/back) of an insurance card uploaded to CyData.
    """

    insurance_member = models.ForeignKey(
        InsuranceMember,
        on_delete=models.CASCADE,
        related_name="cards",
    )
    # CyData file reference URL for front of card
    card_front_url = models.CharField(max_length=500, blank=True)
    # CyData file reference URL for back of card
    card_back_url = models.CharField(max_length=500, blank=True)
    issued_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    is_current = models.BooleanField(default=True)

    class Meta:
        app_label = "cymed_rcm_insurance"
        db_table = "cymed_rcm_ins_cards"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["tenant_id", "is_current"]),
        ]

    def __str__(self):
        return f"InsuranceCard({self.insurance_member_id} | current={self.is_current})"
