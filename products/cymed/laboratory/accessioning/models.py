"""
CyMed Laboratory â€” Accessioning
Unique accession number assignment, multi-site support, reference lab routing.
"""

from django.db import models

from platform.common.models import BaseModel


class AccessionNumberSequence(BaseModel):
    """Per-site, per-year accession number counter. Locked for atomic increment."""

    site_code = models.CharField(max_length=20)
    year = models.PositiveSmallIntegerField()
    last_sequence = models.PositiveBigIntegerField(default=0)
    prefix = models.CharField(max_length=10, default="ACC")

    class Meta:
        db_table = "cymed_lab_accession_sequences"
        unique_together = [("tenant_id", "site_code", "year")]

    def next_number(self) -> str:
        """Atomically increments and returns formatted accession number."""
        from django.db import transaction

        with transaction.atomic():
            obj = AccessionNumberSequence.objects.select_for_update().get(pk=self.pk)
            obj.last_sequence += 1
            obj.save(update_fields=["last_sequence"])
            return f"{obj.prefix}-{obj.site_code}-{obj.year}-{obj.last_sequence:06d}"


class Accession(BaseModel):
    """Accession record linking a specimen to a unique accession number."""

    STATUS_CHOICES = [
        ("active", "Active"),
        ("cancelled", "Cancelled"),
        ("referred", "Referred to Reference Lab"),
        ("completed", "Completed"),
    ]

    accession_number = models.CharField(max_length=100, unique=True, db_index=True)
    specimen = models.OneToOneField(
        "lab_specimens.Specimen", on_delete=models.CASCADE, related_name="accession"
    )
    site_code = models.CharField(max_length=20, blank=True)
    accessioned_at = models.DateTimeField(auto_now_add=True)
    accessioned_by = models.UUIDField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")
    priority_override = models.CharField(max_length=20, blank=True)
    routing_destination = models.CharField(max_length=255, blank=True)  # dept or reference lab
    is_referred = models.BooleanField(default=False)

    class Meta:
        db_table = "cymed_lab_accessions"

    def __str__(self):
        return self.accession_number


class AccessionBatch(BaseModel):
    """Groups multiple accessions processed together (e.g., morning batch run)."""

    batch_number = models.CharField(max_length=100, unique=True)
    site_code = models.CharField(max_length=20, blank=True)
    created_by = models.UUIDField()
    opened_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    accession_count = models.PositiveIntegerField(default=0)
    notes = models.TextField(blank=True)
    is_open = models.BooleanField(default=True)

    class Meta:
        db_table = "cymed_lab_accession_batches"


class AccessionBatchItem(BaseModel):
    """Links an accession to a batch."""

    batch = models.ForeignKey(AccessionBatch, on_delete=models.CASCADE, related_name="items")
    accession = models.ForeignKey(Accession, on_delete=models.CASCADE, related_name="batch_items")
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "cymed_lab_accession_batch_items"
        unique_together = [("batch", "accession")]


class AccessionAudit(BaseModel):
    """Immutable audit log for accession lifecycle events."""

    accession = models.ForeignKey(Accession, on_delete=models.CASCADE, related_name="audit_log")
    event_type = models.CharField(max_length=100)
    performed_by = models.UUIDField(null=True, blank=True)
    detail = models.TextField(blank=True)
    event_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "cymed_lab_accession_audit"
        ordering = ["-event_at"]
