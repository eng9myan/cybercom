from django.db import models

from platform.common.models import BaseModel


class ParsedDocument(BaseModel):
    """
    A document (invoice/PO/bank statement) submitted for AI-assisted field
    extraction. Deliberately a review queue, not an auto-poster: extraction
    fills `extracted_data`, a human corrects it into `reviewed_data` and
    marks it reviewed, and creating the real Invoice/PurchaseOrder from that
    is a separate, explicit action elsewhere -- this app's job ends at
    "here's what the AI read off the page", not "and now it's posted".
    """

    DOCUMENT_TYPES = [
        ("invoice", "Invoice"),
        ("purchase_order", "Purchase Order"),
        ("bank_statement", "Bank Statement"),
    ]
    STATUS = [
        ("pending", "Pending"),
        ("parsed", "Parsed"),
        ("failed", "Failed"),
        ("reviewed", "Reviewed"),
    ]

    document_type = models.CharField(max_length=30, choices=DOCUMENT_TYPES)
    file = models.FileField(upload_to="cycom_docai/%Y/%m/")
    original_filename = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default="pending")
    # Raw AI output -- never edited in place, so there's always a record of
    # what the model actually said versus what a human corrected it to.
    extracted_data = models.JSONField(default=dict, blank=True)
    confidence_notes = models.TextField(blank=True)
    error_message = models.TextField(blank=True)
    reviewed_data = models.JSONField(null=True, blank=True)

    class Meta:
        db_table = "cycom_docai_parsed_documents"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["tenant_id", "status"])]

    def __str__(self):
        return f"{self.document_type}:{self.original_filename or self.pk}"
