from django.db import models

from platform.common.models import BaseModel


class Document(BaseModel):
    """
    Generic document store. linked_model/linked_id let any record in any
    other Cycom app (an invoice, a lead, an employee...) attach files
    without each app needing its own upload plumbing.
    """

    title = models.CharField(max_length=255)
    file = models.FileField(upload_to="cycom_documents/%Y/%m/")
    tags = models.JSONField(default=list, blank=True)
    linked_model = models.CharField(max_length=100, blank=True)
    linked_id = models.UUIDField(null=True, blank=True)
    uploaded_by = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "cycom_documents"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["linked_model", "linked_id"]),
        ]

    def __str__(self):
        return self.title
