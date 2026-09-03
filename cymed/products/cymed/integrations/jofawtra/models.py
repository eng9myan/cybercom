from django.db import models

from platform.common.models import BaseModel


class JoFawTraInvoice(BaseModel):
    """Local record of an invoice submitted to JoFawTra."""

    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("submitted", "Submitted"),
        ("validated", "Validated"),
        ("rejected", "Rejected"),
        ("cancelled", "Cancelled"),
    ]

    invoice_number = models.CharField(max_length=100, unique=True)
    patient_mrn = models.CharField(max_length=100, db_index=True)
    provider_npi = models.CharField(max_length=100, db_index=True)
    total_amount = models.DecimalField(max_digits=14, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    currency = models.CharField(max_length=10, default="JOD")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    jofawtra_invoice_id = models.CharField(max_length=255, blank=True, db_index=True)
    jofawtra_qr_code = models.TextField(blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    validated_at = models.DateTimeField(null=True, blank=True)
    raw_payload = models.JSONField(default=dict, blank=True)
    response_payload = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "cymed_jofawtra_invoices"
        ordering = ["-created_at"]

    def __str__(self):
        return f"JoFawTra {self.invoice_number} ({self.status})"
