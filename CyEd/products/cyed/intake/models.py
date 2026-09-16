from django.db import models

from platform.common.models import BaseModel


class DocumentIntake(BaseModel):
    DOC_TYPES = [
        ("birth_certificate", "Birth Certificate"),
        ("transcript", "Transcript"),
        ("receipt", "Receipt"),
        ("id", "ID Document"),
        ("other", "Other"),
    ]
    STATUS = [
        ("uploaded", "Uploaded"),
        ("ocr_pending", "OCR Pending"),
        ("extracted", "Extracted"),
        ("failed", "Failed"),
    ]

    doc_type = models.CharField(max_length=30, choices=DOC_TYPES, default="other")
    student = models.ForeignKey("cyed_sis.Student", on_delete=models.SET_NULL, null=True, blank=True,
                                related_name="documents")
    application_ref = models.CharField(max_length=64, blank=True)
    file_bytes = models.BinaryField(null=True, blank=True)
    content_type = models.CharField(max_length=100, blank=True)
    raw_text = models.TextField(blank=True)
    extracted_fields = models.JSONField(default=dict)
    status = models.CharField(max_length=20, choices=STATUS, default="uploaded")

    class Meta:
        db_table = "cyed_document_intakes"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.doc_type} ({self.status})"
