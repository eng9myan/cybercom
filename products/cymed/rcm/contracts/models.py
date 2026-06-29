from django.db import models

from platform.common.models import BaseModel


class PayerContract(BaseModel):
    CONTRACT_TYPE_CHOICES = [
        ("fee_for_service", "Fee for Service"),
        ("capitation", "Capitation"),
        ("bundled", "Bundled Payment"),
        ("drg", "DRG"),
        ("per_diem", "Per Diem"),
        ("value_based", "Value-Based"),
        ("discount_from_charges", "Discount from Charges"),
    ]
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("active", "Active"),
        ("expired", "Expired"),
        ("terminated", "Terminated"),
        ("pending_renewal", "Pending Renewal"),
    ]

    insurance_company_id = models.UUIDField(db_index=True)
    contract_name = models.CharField(max_length=200)
    contract_number = models.CharField(max_length=100, unique=True, null=True, blank=True)
    contract_type = models.CharField(max_length=30, choices=CONTRACT_TYPE_CHOICES)
    facility_id = models.UUIDField(null=True, blank=True)
    effective_date = models.DateField()
    expiry_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    base_discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    auto_renewal = models.BooleanField(default=False)
    renewal_notice_days = models.PositiveSmallIntegerField(default=90)

    class Meta:
        app_label = "cymed_rcm_contracts"
        db_table = "cymed_rcm_ctr_contracts"
        ordering = ["-effective_date"]
        indexes = [
            models.Index(fields=["tenant_id", "insurance_company_id"]),
            models.Index(fields=["tenant_id", "status"]),
        ]

    def __str__(self):
        return f"PayerContract({self.contract_name} | {self.status})"


class ContractRate(BaseModel):
    RATE_TYPE_CHOICES = [
        ("flat_fee", "Flat Fee"),
        ("percentage", "Percentage"),
        ("per_diem", "Per Diem"),
        ("case_rate", "Case Rate"),
        ("drg", "DRG"),
    ]

    contract = models.ForeignKey(PayerContract, on_delete=models.CASCADE, related_name="rates")
    service_code = models.CharField(max_length=50)
    service_description = models.CharField(max_length=500, blank=True)
    rate_type = models.CharField(max_length=20, choices=RATE_TYPE_CHOICES)
    rate_amount = models.DecimalField(max_digits=12, decimal_places=2)
    rate_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    effective_date = models.DateField()
    expiry_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        app_label = "cymed_rcm_contracts"
        db_table = "cymed_rcm_ctr_rates"
        ordering = ["service_code"]
        unique_together = [["tenant_id", "contract", "service_code", "effective_date"]]
        indexes = [models.Index(fields=["tenant_id", "contract_id", "service_code"])]

    def __str__(self):
        return f"ContractRate({self.service_code} | {self.rate_type} | {self.rate_amount})"


class ContractRule(BaseModel):
    RULE_TYPE_CHOICES = [
        ("preauth_required", "Preauth Required"),
        ("timely_filing", "Timely Filing"),
        ("coordination_of_benefits", "Coordination of Benefits"),
        ("billing_restriction", "Billing Restriction"),
        ("exclusion", "Exclusion"),
        ("bundling", "Bundling"),
        ("global_period", "Global Period"),
    ]

    contract = models.ForeignKey(PayerContract, on_delete=models.CASCADE, related_name="rules")
    rule_type = models.CharField(max_length=30, choices=RULE_TYPE_CHOICES)
    rule_description = models.TextField()
    applies_to_service_codes = models.JSONField(default=list)
    days_limit = models.PositiveIntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        app_label = "cymed_rcm_contracts"
        db_table = "cymed_rcm_ctr_rules"
        ordering = ["rule_type"]
        indexes = [models.Index(fields=["tenant_id", "contract_id", "rule_type"])]

    def __str__(self):
        return f"ContractRule({self.rule_type} | contract={self.contract_id})"


class ReimbursementRule(BaseModel):
    CALCULATION_METHOD_CHOICES = [
        ("percent_of_charges", "Percent of Charges"),
        ("fixed_rate", "Fixed Rate"),
        ("drg_multiplier", "DRG Multiplier"),
        ("case_rate", "Case Rate"),
        ("capitation", "Capitation"),
    ]

    contract = models.ForeignKey(
        PayerContract, on_delete=models.CASCADE, related_name="reimbursement_rules"
    )
    rule_name = models.CharField(max_length=200)
    calculation_method = models.CharField(max_length=30, choices=CALCULATION_METHOD_CHOICES)
    base_rate = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    percentage_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    applies_to_categories = models.JSONField(default=list)
    max_reimbursement = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        app_label = "cymed_rcm_contracts"
        db_table = "cymed_rcm_ctr_reimbursement_rules"
        ordering = ["rule_name"]
        indexes = [models.Index(fields=["tenant_id", "contract_id"])]

    def __str__(self):
        return f"ReimbursementRule({self.rule_name} | {self.calculation_method})"
