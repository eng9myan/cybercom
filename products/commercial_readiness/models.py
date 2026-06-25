from django.db import models
from platform.common.models import BaseModel


PLAN_TYPE_CHOICES = [
    ("per_user", "Per User"),
    ("per_bed", "Per Bed"),
    ("per_transaction", "Per Transaction"),
    ("flat_fee", "Flat Fee"),
    ("usage_based", "Usage Based"),
    ("enterprise", "Enterprise"),
]

BILLING_CYCLE_CHOICES = [
    ("monthly", "Monthly"),
    ("annual", "Annual"),
    ("one_time", "One Time"),
]

QUOTATION_STATUS_CHOICES = [
    ("draft", "Draft"),
    ("sent", "Sent"),
    ("accepted", "Accepted"),
    ("rejected", "Rejected"),
    ("expired", "Expired"),
]

PROPOSAL_STATUS_CHOICES = [
    ("draft", "Draft"),
    ("review", "Review"),
    ("submitted", "Submitted"),
    ("won", "Won"),
    ("lost", "Lost"),
]

COMPLIANCE_STANDARD_CHOICES = [
    ("hipaa", "HIPAA"),
    ("gdpr", "GDPR"),
    ("pdpl", "PDPL"),
    ("iso27001", "ISO 27001"),
    ("soc2", "SOC 2"),
    ("jcia", "JCIA"),
    ("cbahi", "CBAHI"),
    ("fhir_r4", "FHIR R4"),
    ("hl7_v2", "HL7 v2"),
    ("dicom", "DICOM"),
]

COMPLIANCE_STATUS_CHOICES = [
    ("certified", "Certified"),
    ("in_progress", "In Progress"),
    ("planned", "Planned"),
    ("not_applicable", "Not Applicable"),
]

BENCHMARK_CATEGORY_CHOICES = [
    ("features", "Features"),
    ("pricing", "Pricing"),
    ("performance", "Performance"),
    ("security", "Security"),
    ("compliance", "Compliance"),
    ("support", "Support"),
    ("scalability", "Scalability"),
]


class PricingPlan(BaseModel):
    class Meta:
        app_label = "cybercom_cr"
        db_table = "cybercom_cr_pricing_plan"

    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50, unique=True)
    product_code = models.CharField(max_length=50, db_index=True)
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPE_CHOICES)
    base_price = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=10, default="USD")
    billing_cycle = models.CharField(max_length=20, choices=BILLING_CYCLE_CHOICES)
    min_units = models.PositiveIntegerField(default=1)
    max_units = models.PositiveIntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    country_codes = models.JSONField(default=list)

    def __str__(self):
        return f"{self.name} ({self.code}) — {self.plan_type}"


class Quotation(BaseModel):
    class Meta:
        app_label = "cybercom_cr"
        db_table = "cybercom_cr_quotation"

    quote_number = models.CharField(max_length=100, unique=True)
    customer_name = models.CharField(max_length=200)
    customer_email = models.EmailField()
    customer_organization = models.CharField(max_length=200, blank=True)
    sales_rep_id = models.UUIDField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=QUOTATION_STATUS_CHOICES, default="draft")
    line_items = models.JSONField(default=list)
    subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    discount_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    currency = models.CharField(max_length=10, default="USD")
    valid_until = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    accepted_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Quote {self.quote_number} — {self.customer_name} ({self.status})"


class Proposal(BaseModel):
    class Meta:
        app_label = "cybercom_cr"
        db_table = "cybercom_cr_proposal"

    opportunity_id = models.CharField(max_length=100, db_index=True)
    customer_name = models.CharField(max_length=200)
    proposal_title = models.CharField(max_length=300)
    status = models.CharField(max_length=20, choices=PROPOSAL_STATUS_CHOICES, default="draft")
    rfp_reference = models.CharField(max_length=200, blank=True)
    executive_summary = models.TextField(blank=True)
    solution_scope = models.JSONField(default=list)
    proposed_modules = models.JSONField(default=list)
    total_value = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    currency = models.CharField(max_length=10, default="USD")
    submission_date = models.DateField(null=True, blank=True)
    decision_date = models.DateField(null=True, blank=True)
    win_reason = models.TextField(blank=True)
    loss_reason = models.TextField(blank=True)

    def __str__(self):
        return f"{self.proposal_title} — {self.customer_name} ({self.status})"


class LicenseKey(BaseModel):
    class Meta:
        app_label = "cybercom_cr"
        db_table = "cybercom_cr_license_key"

    customer_id = models.UUIDField(db_index=True)
    product_code = models.CharField(max_length=50, db_index=True)
    edition = models.CharField(max_length=50, blank=True)
    key_value = models.CharField(max_length=200, unique=True)
    issued_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    max_users = models.PositiveIntegerField(null=True, blank=True)
    max_beds = models.PositiveIntegerField(null=True, blank=True)
    licensed_modules = models.JSONField(default=list)
    is_active = models.BooleanField(default=True)
    activated_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"License {self.key_value[:20]}... — {self.product_code}"


class ComplianceCertification(BaseModel):
    class Meta:
        app_label = "cybercom_cr"
        db_table = "cybercom_cr_compliance_cert"

    product_code = models.CharField(max_length=50, db_index=True)
    standard = models.CharField(max_length=20, choices=COMPLIANCE_STANDARD_CHOICES)
    status = models.CharField(max_length=20, choices=COMPLIANCE_STATUS_CHOICES, default="planned")
    certified_at = models.DateField(null=True, blank=True)
    expires_at = models.DateField(null=True, blank=True)
    certificate_url = models.URLField(blank=True)
    auditor_name = models.CharField(max_length=200, blank=True)
    scope_description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.product_code} — {self.standard} ({self.status})"


class CompetitiveBenchmark(BaseModel):
    class Meta:
        app_label = "cybercom_cr"
        db_table = "cybercom_cr_competitive_benchmark"

    product_code = models.CharField(max_length=50, db_index=True)
    competitor_name = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=BENCHMARK_CATEGORY_CHOICES)
    our_score = models.DecimalField(max_digits=4, decimal_places=1)
    competitor_score = models.DecimalField(max_digits=4, decimal_places=1)
    benchmark_notes = models.TextField(blank=True)
    last_updated = models.DateField()

    def __str__(self):
        return f"{self.product_code} vs {self.competitor_name} — {self.category}"
