"""
E-invoicing & tax compliance.

    Invoice / InvoiceLine   the tax invoice itself (standard B2B or simplified B2C)
    TaxProfile              per-company seller identity + which scheme applies
    EInvoiceDocument        the compliance artifact — UBL 2.1 XML, invoice hash,
                            ZATCA-style TLV QR, and the submission lifecycle

Scheme is pluggable (`none` / `zatca` / `jofotara`); the XML + QR + hash are
generated locally. Cryptographic signing and live submission to ZATCA / JoFotara
need the founder's onboarded CSID / client credentials — see `services.submit`.
"""
from decimal import Decimal

from django.db import models

from apps.tenants.models import BaseEntity, Company

Z2 = Decimal("0.01")


class TaxProfile(BaseEntity):
    SCHEMES = [("none", "None / not required"),
               ("zatca", "ZATCA (Saudi Arabia)"),
               ("jofotara", "JoFotara (Jordan)")]

    company = models.OneToOneField(Company, on_delete=models.CASCADE, related_name="tax_profile")
    scheme = models.CharField(max_length=12, choices=SCHEMES, default="none")
    legal_name = models.CharField(max_length=255)
    legal_name_ar = models.CharField(max_length=255, blank=True)
    vat_number = models.CharField(max_length=50, blank=True)
    tax_scheme_id = models.CharField(max_length=20, default="VAT")
    country_code = models.CharField(max_length=2, default="SA")
    address_street = models.CharField(max_length=255, blank=True)
    address_city = models.CharField(max_length=120, blank=True)
    address_postal = models.CharField(max_length=20, blank=True)
    # scheme onboarding (set by the founder once the seller is registered)
    csid = models.TextField(blank=True, help_text="Compliance/Production CSID (base64)")
    client_id = models.CharField(max_length=255, blank=True)
    client_secret = models.CharField(max_length=255, blank=True)
    default_vat_rate = models.DecimalField(max_digits=5, decimal_places=4, default=Decimal("0.15"))

    class Meta:
        db_table = "einvoicing_tax_profiles"

    def __str__(self):
        return f"{self.legal_name} [{self.scheme}]"


class Invoice(BaseEntity):
    TYPES = [("standard", "Standard tax invoice (B2B)"),
             ("simplified", "Simplified tax invoice (B2C)"),
             ("credit_note", "Credit note"), ("debit_note", "Debit note")]
    STATUS = [("draft", "Draft"), ("issued", "Issued"), ("paid", "Paid"),
              ("void", "Void")]

    number = models.CharField(max_length=60)
    company = models.ForeignKey(Company, on_delete=models.PROTECT, related_name="invoices")
    invoice_type = models.CharField(max_length=12, choices=TYPES, default="simplified")
    status = models.CharField(max_length=10, choices=STATUS, default="draft")

    customer_name = models.CharField(max_length=255)
    customer_tax_number = models.CharField(max_length=50, blank=True)
    customer_address = models.CharField(max_length=255, blank=True)

    issue_date = models.DateField()
    supply_date = models.DateField(null=True, blank=True)
    currency = models.CharField(max_length=3, default="SAR")

    # links to what was sold (optional)
    source_type = models.CharField(max_length=20, blank=True)   # pos_order | sales_order
    source_id = models.UUIDField(null=True, blank=True)
    corrected_invoice = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True, related_name="corrections")

    subtotal = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    discount_total = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    tax_total = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "einvoicing_invoices"
        unique_together = [("tenant_id", "number")]
        ordering = ["-issue_date", "-created_at"]

    def recalculate(self, save=True):
        lines = self.lines.filter(is_deleted=False)
        sub = sum((l.line_subtotal for l in lines), Decimal("0"))
        tax = sum((l.line_tax for l in lines), Decimal("0"))
        self.subtotal = sub.quantize(Z2)
        self.tax_total = tax.quantize(Z2)
        self.total = (sub + tax - Decimal(self.discount_total or 0)).quantize(Z2)
        if save:
            self.save(update_fields=["subtotal", "tax_total", "total", "updated_at", "version"])

    def __str__(self):
        return f"{self.number} — {self.customer_name} ({self.total} {self.currency})"


class InvoiceLine(BaseEntity):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="lines")
    line_no = models.PositiveIntegerField(default=1)
    description = models.CharField(max_length=255)
    quantity = models.DecimalField(max_digits=15, decimal_places=4, default=1)
    unit_price = models.DecimalField(max_digits=15, decimal_places=4, default=0)
    discount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=4, default=Decimal("0.15"))

    class Meta:
        db_table = "einvoicing_invoice_lines"
        ordering = ["line_no"]

    @property
    def line_subtotal(self) -> Decimal:
        return (self.quantity * self.unit_price - Decimal(self.discount or 0)).quantize(Z2)

    @property
    def line_tax(self) -> Decimal:
        return (self.line_subtotal * Decimal(self.tax_rate)).quantize(Z2)

    @property
    def line_total(self) -> Decimal:
        return (self.line_subtotal + self.line_tax).quantize(Z2)


class EInvoiceDocument(BaseEntity):
    STATUS = [
        ("draft", "Draft"),
        ("generated", "XML generated"),
        ("signed", "Signed"),
        ("submitted", "Submitted"),
        ("cleared", "Cleared"),          # ZATCA standard invoice
        ("reported", "Reported"),        # ZATCA simplified / JoFotara
        ("rejected", "Rejected"),
    ]

    invoice = models.OneToOneField(Invoice, on_delete=models.CASCADE, related_name="einvoice")
    scheme = models.CharField(max_length=12, default="none")
    status = models.CharField(max_length=12, choices=STATUS, default="draft")

    uuid = models.UUIDField(null=True, blank=True)           # invoice UUID (UBL cbc:UUID)
    icv = models.PositiveBigIntegerField(default=1)          # invoice counter value
    pih = models.CharField(max_length=100, blank=True)       # previous invoice hash (base64)
    invoice_hash = models.CharField(max_length=100, blank=True)
    qr_code = models.TextField(blank=True)                   # base64 TLV
    ubl_xml = models.TextField(blank=True)
    signed_xml = models.TextField(blank=True)

    submitted_at = models.DateTimeField(null=True, blank=True)
    cleared_at = models.DateTimeField(null=True, blank=True)
    submission_response = models.JSONField(default=dict, blank=True)
    warnings = models.JSONField(default=list, blank=True)
    error = models.TextField(blank=True)

    class Meta:
        db_table = "einvoicing_documents"

    def __str__(self):
        return f"E-invoice {self.invoice.number} [{self.scheme}/{self.status}]"
