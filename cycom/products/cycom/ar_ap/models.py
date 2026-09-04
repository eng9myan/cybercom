from decimal import Decimal

from django.db import models

from platform.common.fields import EncryptedText
from platform.common.models import BaseModel
from products.cycom.accounting.models import Account, JournalEntry


class Partner(BaseModel):
    PARTNER_TYPES = [
        ("customer", "Customer"),
        ("vendor", "Vendor"),
        ("both", "Customer & Vendor"),
    ]
    CATEGORY_CHOICES = [
        ("goods", "Goods & Supply"),
        ("services", "Operational Services"),
        ("both", "Both Goods & Services"),
    ]
    APPROVAL_STATUS_CHOICES = [
        ("draft", "Draft"),
        ("submitted", "Submitted"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]

    name = models.CharField(max_length=255)
    partner_type = models.CharField(max_length=20, choices=PARTNER_TYPES, default="customer")
    # Contact PII — encrypted per-tenant. email is blind-indexed for exact match.
    email = EncryptedText(classification="pii", blind_index=True)
    phone = EncryptedText(classification="pii")
    # Business tax ID — semi-public, used for e-invoicing buyer-VAT routing; left plain.
    tax_id = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)

    # Vendor onboarding/compliance fields (cycom-erp's Supplier Registration
    # Wizard) — only meaningful for partner_type=vendor, left blank otherwise.
    legal_name_ar = models.CharField(max_length=255, blank=True)
    trade_name = models.CharField(max_length=255, blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default="goods")
    cr_number = models.CharField(max_length=100, blank=True)
    cr_expiry = models.DateField(null=True, blank=True)
    bank_name = models.CharField(max_length=255, blank=True)
    bank_branch = models.CharField(max_length=255, blank=True)
    # financial identifier — encrypted per-tenant (platform.common.fields).
    # blind_index so a partner can still be found by exact IBAN.
    iban = EncryptedText(classification="financial_id", blind_index=True)
    swift_code = models.CharField(max_length=20, blank=True)
    credit_limit = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    payment_terms_days = models.PositiveIntegerField(default=30)
    contact_name = EncryptedText(classification="pii")
    address = EncryptedText(classification="pii")
    city = models.CharField(max_length=100, blank=True)
    approval_status = models.CharField(
        max_length=20, choices=APPROVAL_STATUS_CHOICES, default="draft"
    )
    rejection_reason = models.TextField(blank=True)

    class Meta:
        db_table = "cycom_arap_partners"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Invoice(BaseModel):
    """Customer invoice (AR) or vendor bill (AP)."""

    INVOICE_TYPES = [
        ("customer", "Customer Invoice"),
        ("vendor", "Vendor Bill"),
    ]
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("posted", "Posted"),
        ("partial", "Partially Paid"),
        ("paid", "Paid"),
        ("cancelled", "Cancelled"),
    ]

    invoice_type = models.CharField(max_length=20, choices=INVOICE_TYPES)
    number = models.CharField(max_length=100)
    partner = models.ForeignKey(Partner, on_delete=models.PROTECT, related_name="invoices")
    date = models.DateField()
    due_date = models.DateField()
    currency = models.CharField(max_length=10, default="JOD")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")

    # Control account (Accounts Receivable for customer invoices, Accounts
    # Payable for vendor bills) and the tax liability account — set per
    # invoice rather than hardcoded so different tenants can use different
    # charts of accounts.
    control_account = models.ForeignKey(
        Account, on_delete=models.PROTECT, related_name="invoices_as_control"
    )
    tax_account = models.ForeignKey(
        Account, on_delete=models.PROTECT, related_name="invoices_as_tax", null=True, blank=True
    )

    amount_subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    amount_tax = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    amount_total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    amount_paid = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    journal_entry = models.ForeignKey(
        JournalEntry, on_delete=models.PROTECT, null=True, blank=True, related_name="+"
    )
    # Vendor bills may link to the PO they settle, enabling 3-way matching
    # (PO ordered ↔ goods received ↔ this bill). String ref avoids an
    # ar_ap→procurement import cycle (procurement already imports ar_ap).
    purchase_order = models.ForeignKey(
        "cycom_procurement.PurchaseOrder", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="vendor_bills",
    )

    # ── E-invoicing (JoFotara / ZATCA / Peppol) — populated by
    #    platform.einvoicing.engine.clear_invoice after the invoice is posted.
    #    All nullable: an invoice in a country with no e-invoicing mandate, or
    #    issued before clearance ran, simply has einvoice_status="none".
    einvoice_mode = models.CharField(max_length=16, blank=True)
    einvoice_uuid = models.UUIDField(null=True, blank=True)
    einvoice_icv = models.PositiveBigIntegerField(null=True, blank=True)
    einvoice_pih = models.TextField(blank=True)
    einvoice_hash = models.TextField(blank=True)
    einvoice_qr = models.TextField(blank=True)
    einvoice_status = models.CharField(max_length=16, default="none")
    einvoice_reference = models.CharField(max_length=200, blank=True)
    einvoice_response = models.JSONField(default=dict, blank=True)
    einvoice_cleared_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "cycom_arap_invoices"
        unique_together = [("tenant_id", "number")]
        ordering = ["-date", "-created_at"]

    @property
    def amount_due(self):
        return self.amount_total - self.amount_paid

    def __str__(self):
        return f"{self.number} ({self.status})"


class InvoiceLine(BaseModel):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="lines")
    account = models.ForeignKey(Account, on_delete=models.PROTECT, related_name="invoice_lines")
    description = models.CharField(max_length=255, blank=True)
    quantity = models.DecimalField(max_digits=12, decimal_places=4, default=1)
    unit_price = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    tax_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    class Meta:
        db_table = "cycom_arap_invoice_lines"
        ordering = ["id"]

    @property
    def subtotal(self):
        return self.quantity * self.unit_price

    @property
    def tax_amount(self):
        return (self.subtotal * self.tax_percent / 100).quantize(Decimal("0.01"))


class Payment(BaseModel):
    """Cash/bank payment applied against a single invoice or bill."""

    partner = models.ForeignKey(Partner, on_delete=models.PROTECT, related_name="payments")
    invoice = models.ForeignKey(Invoice, on_delete=models.PROTECT, related_name="payments")
    cash_account = models.ForeignKey(Account, on_delete=models.PROTECT, related_name="payments")
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    date = models.DateField()
    method = models.CharField(max_length=20, default="bank")  # bank | cash
    status = models.CharField(
        max_length=20, choices=[("draft", "Draft"), ("posted", "Posted")], default="draft"
    )
    journal_entry = models.ForeignKey(
        JournalEntry, on_delete=models.PROTECT, null=True, blank=True, related_name="+"
    )

    class Meta:
        db_table = "cycom_arap_payments"
        ordering = ["-date", "-created_at"]
