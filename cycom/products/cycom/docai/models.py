from django.db import models

from platform.common.models import BaseModel


class ParsedDocument(BaseModel):
    """
    A document (invoice/PO/bank statement) submitted for AI-assisted field
    extraction. Deliberately a review queue, not an auto-poster: extraction
    fills `extracted_data`, a human corrects it into `reviewed_data` and
    marks it reviewed, and only then can an explicit `apply` step turn the
    reviewed data into a real *draft* Invoice/PurchaseOrder (see
    `products.cycom.docai.apply`). Nothing is ever posted to the ledger or
    approved from here -- the created record goes through the normal
    post/approve flow like any hand-entered one.
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
        ("applied", "Applied"),
    ]
    APPLIED_RECORD_TYPES = [
        ("invoice", "Invoice"),
        ("purchase_order", "Purchase Order"),
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
    # The real record created by `apply`. A plain type+id pair rather than
    # two nullable FKs: docai stays a leaf app that ar_ap/procurement never
    # need to know about.
    applied_record_type = models.CharField(max_length=30, choices=APPLIED_RECORD_TYPES, blank=True)
    applied_record_id = models.UUIDField(null=True, blank=True)

    class Meta:
        db_table = "cycom_docai_parsed_documents"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["tenant_id", "status"])]

    def __str__(self):
        return f"{self.document_type}:{self.original_filename or self.pk}"
