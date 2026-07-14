from django.db import models

from platform.common.models import BaseModel


class PatientAccount(BaseModel):
    """
    Central billing account for a patient within a tenant.
    Tracks insurance assignments, balances, and account lifecycle.
    """

    ACCOUNT_STATUS_CHOICES = [
        ("active", "Active"),
        ("inactive", "Inactive"),
        ("suspended", "Suspended"),
        ("closed", "Closed"),
    ]

    GUARANTOR_TYPE_CHOICES = [
        ("self", "Self"),
        ("parent", "Parent"),
        ("spouse", "Spouse"),
        ("employer", "Employer"),
        ("government", "Government"),
        ("other", "Other"),
    ]

    patient_id = models.UUIDField(db_index=True)
    account_number = models.CharField(max_length=50, unique=True)
    account_status = models.CharField(
        max_length=20,
        choices=ACCOUNT_STATUS_CHOICES,
        default="active",
    )
    guarantor_patient_id = models.UUIDField(null=True, blank=True)
    guarantor_type = models.CharField(
        max_length=20,
        choices=GUARANTOR_TYPE_CHOICES,
        default="self",
    )
    primary_insurance_member_id = models.UUIDField(null=True, blank=True)
    secondary_insurance_member_id = models.UUIDField(null=True, blank=True)
    tertiary_insurance_member_id = models.UUIDField(null=True, blank=True)
    credit_balance = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    outstanding_balance = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    fhir_account_id = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        db_table = "cymed_rcm_bill_patient_accounts"
        unique_together = [["tenant_id", "patient_id"]]
        ordering = ["-created_at"]

    def __str__(self):
        return f"PatientAccount {self.account_number}"


class EncounterBilling(BaseModel):
    """
    Billing record tied to a single clinical encounter.
    Aggregates charges, expected insurance, and patient responsibility.
    """

    ENCOUNTER_TYPE_CHOICES = [
        ("outpatient", "Outpatient"),
        ("inpatient", "Inpatient"),
        ("emergency", "Emergency"),
        ("day_case", "Day Case"),
        ("telemedicine", "Telemedicine"),
        ("home_visit", "Home Visit"),
        ("lab", "Laboratory"),
        ("imaging", "Imaging"),
        ("pharmacy", "Pharmacy"),
    ]

    BILLING_STATUS_CHOICES = [
        ("open", "Open"),
        ("coded", "Coded"),
        ("reviewed", "Reviewed"),
        ("billed", "Billed"),
        ("paid", "Paid"),
        ("partial", "Partial"),
        ("denied", "Denied"),
        ("written_off", "Written Off"),
    ]

    patient_account = models.ForeignKey(
        PatientAccount,
        on_delete=models.PROTECT,
        related_name="encounter_billings",
    )
    encounter_id = models.UUIDField(db_index=True)
    encounter_type = models.CharField(max_length=30, choices=ENCOUNTER_TYPE_CHOICES)
    encounter_date = models.DateField()
    facility_id = models.UUIDField(db_index=True)
    attending_provider_id = models.UUIDField(db_index=True)
    department_id = models.UUIDField(null=True, blank=True)
    billing_status = models.CharField(
        max_length=20,
        choices=BILLING_STATUS_CHOICES,
        default="open",
    )
    total_charges = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    insurance_expected = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    patient_responsibility = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    amount_paid = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    balance_due = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    icd11_primary_diagnosis = models.CharField(max_length=20, blank=True)
    icd11_secondary_diagnoses = models.JSONField(default=list)

    class Meta:
        db_table = "cymed_rcm_bill_encounter_billings"
        unique_together = [["tenant_id", "encounter_id"]]
        ordering = ["-encounter_date"]

    def __str__(self):
        return f"EncounterBilling {self.encounter_id} ({self.billing_status})"


class Invoice(BaseModel):
    """
    Financial invoice issued to a patient, insurance company, or corporate entity.
    """

    INVOICE_TYPE_CHOICES = [
        ("patient", "Patient"),
        ("insurance", "Insurance"),
        ("corporate", "Corporate"),
        ("government", "Government"),
    ]

    BILLING_PARTY_TYPE_CHOICES = [
        ("insurance", "Insurance"),
        ("corporate", "Corporate"),
        ("government", "Government"),
        ("self_pay", "Self Pay"),
    ]

    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("issued", "Issued"),
        ("sent", "Sent"),
        ("partial", "Partial"),
        ("paid", "Paid"),
        ("overdue", "Overdue"),
        ("cancelled", "Cancelled"),
        ("written_off", "Written Off"),
    ]

    patient_account = models.ForeignKey(
        PatientAccount,
        on_delete=models.PROTECT,
        related_name="invoices",
    )
    encounter_billing = models.ForeignKey(
        EncounterBilling,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="invoices",
    )
    invoice_number = models.CharField(max_length=50, unique=True)
    invoice_type = models.CharField(max_length=20, choices=INVOICE_TYPE_CHOICES)
    invoice_date = models.DateField()
    due_date = models.DateField()
    billing_party_id = models.UUIDField(null=True, blank=True)
    billing_party_type = models.CharField(
        max_length=20,
        blank=True,
        choices=BILLING_PARTY_TYPE_CHOICES,
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    amount_subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    amount_tax = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    amount_discount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    amount_total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    amount_paid = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    amount_outstanding = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default="SAR")
    notes = models.TextField(blank=True)
    fhir_invoice_id = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        db_table = "cymed_rcm_bill_invoices"
        ordering = ["-invoice_date"]

    def __str__(self):
        return f"Invoice {self.invoice_number} ({self.status})"


class InvoiceLine(BaseModel):
    """
    Individual line item on an invoice representing a service or charge.
    """

    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name="lines",
    )
    line_number = models.PositiveSmallIntegerField(default=1)
    service_date = models.DateField()
    service_code = models.CharField(max_length=50)
    service_description = models.CharField(max_length=500)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    line_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    charge_id = models.UUIDField(null=True, blank=True)
    icd11_diagnosis_code = models.CharField(max_length=20, blank=True)

    class Meta:
        db_table = "cymed_rcm_bill_invoice_lines"
        ordering = ["line_number"]

    def __str__(self):
        return f"InvoiceLine {self.line_number} on Invoice {self.invoice_id}"


class BillingAdjustment(BaseModel):
    """
    Financial adjustment applied to an invoice (contractual, write-off, discount, etc.).
    """

    ADJUSTMENT_TYPE_CHOICES = [
        ("contractual", "Contractual"),
        ("write_off", "Write Off"),
        ("discount", "Discount"),
        ("refund", "Refund"),
        ("correction", "Correction"),
        ("insurance_writeoff", "Insurance Write-Off"),
        ("bad_debt", "Bad Debt"),
        ("courtesy", "Courtesy"),
    ]

    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name="adjustments",
    )
    adjustment_type = models.CharField(max_length=30, choices=ADJUSTMENT_TYPE_CHOICES)
    adjustment_amount = models.DecimalField(max_digits=12, decimal_places=2)
    adjustment_date = models.DateField(auto_now_add=True)
    reason = models.TextField(blank=True)
    approved_by_user_id = models.UUIDField(null=True, blank=True)

    class Meta:
        db_table = "cymed_rcm_bill_adjustments"
        ordering = ["-adjustment_date"]

    def __str__(self):
        return f"BillingAdjustment {self.adjustment_type} on Invoice {self.invoice_id}"


class Refund(BaseModel):
    """
    Refund issued against a paid invoice.
    """

    REFUND_METHOD_CHOICES = [
        ("cash", "Cash"),
        ("card", "Card"),
        ("bank_transfer", "Bank Transfer"),
        ("cheque", "Cheque"),
        ("credit_note", "Credit Note"),
        ("insurance_reversal", "Insurance Reversal"),
    ]

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("processed", "Processed"),
        ("rejected", "Rejected"),
    ]

    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.PROTECT,
        related_name="refunds",
    )
    refund_amount = models.DecimalField(max_digits=12, decimal_places=2)
    refund_method = models.CharField(max_length=20, choices=REFUND_METHOD_CHOICES)
    refund_date = models.DateField()
    reason = models.TextField(blank=True)
    processed_by_user_id = models.UUIDField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    class Meta:
        db_table = "cymed_rcm_bill_refunds"
        ordering = ["-refund_date"]

    def __str__(self):
        return f"Refund {self.refund_amount} on Invoice {self.invoice_id} ({self.status})"
