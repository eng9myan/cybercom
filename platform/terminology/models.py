import uuid

from django.db import models
from django.utils import timezone


class TerminologyAuditLog(models.Model):
    """
    Audit ledger tracking clinical terminology requests.
    Enforces multi-tenant visibility and records performance metrics.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(db_index=True)
    provider = models.CharField(max_length=100, db_index=True)  # icd11, snomed, loinc, etc.
    operation = models.CharField(
        max_length=100, db_index=True
    )  # search, lookup, validate, translate, expand
    query = models.CharField(max_length=1000, blank=True)
    code = models.CharField(max_length=500, blank=True)
    records_returned = models.PositiveIntegerField(default=0)
    duration_ms = models.PositiveIntegerField(default=0)
    requested_by = models.CharField(max_length=255, blank=True)
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        db_table = "platform_terminology_audit_logs"
        ordering = ["-timestamp"]

    def __str__(self) -> str:
        return f"TerminologyAudit({self.tenant_id}, {self.provider}, {self.operation}, {self.timestamp})"
