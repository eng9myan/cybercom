from django.db import models

from platform.common.models import BaseModel


class QualityCheckpoint(BaseModel):
    """
    Generic quality gate — linked_model/linked_id points at whatever record
    triggered the check (a StockMove, a ManufacturingOrder, ...), same
    generic-link pattern used by Documents/Calendar/To-Do.
    """

    RESULT_CHOICES = [
        ("pending", "Pending"),
        ("pass", "Pass"),
        ("fail", "Fail"),
    ]

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    linked_model = models.CharField(max_length=100, blank=True)
    linked_id = models.UUIDField(null=True, blank=True)
    result = models.CharField(max_length=10, choices=RESULT_CHOICES, default="pending")
    checked_by = models.CharField(max_length=255, blank=True)
    checked_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "cycom_quality_checkpoints"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["linked_model", "linked_id"])]

    def __str__(self):
        return f"{self.name} ({self.result})"
