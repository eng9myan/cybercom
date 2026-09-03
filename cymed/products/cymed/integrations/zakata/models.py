from django.db import models

from platform.common.models import BaseModel


class ZATCAInvoice(BaseModel):
    """Local record of a Saudi ZATCA e-invoice."""

    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("reported", "Reported"),
        ("cleared", "Cleared"),
        ("rejected", "Rejected"),
        ("cancelled", "Cancelled"),
    ]

    INVOICE_TYPE_CHOICES = [
        ("b2c", "B2C — Simplified"),
        ("b2b", "B2B — Standard"),
    ]

    invoice_number = models.CharField(max_length=100, unique=True)
    invoice_type = models.CharField(max_length=10, choices=INVOICE_TYPE_CHOICES, default="b2c")
    patient_mrn = models.CharField(max_length=100, db_index=True)
    provider_npi = models.CharField(max_length=100, db_index=True)
    total_amount = models.DecimalField(max_digits=14, decimal_places=2)
    vat_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_with_vat = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    currency = models.CharField(max_length=10, default="SAR")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    zatca_invoice_uuid = models.CharField(max_length=255, blank=True, db_index=True)
    qr_code_data = models.TextField(blank=True)
    xml_payload = models.TextField(blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    cleared_at = models.DateTimeField(null=True, blank=True)
    response_payload = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "cymed_zakata_invoices"
        ordering = ["-created_at"]

    def __str__(self):
        return f"ZATCA {self.invoice_number} ({self.status})"
