from django.db import models
from django.utils import timezone

from platform.common.models import BaseModel
from products.cymed.core.patients.models import Patient


class CohortRegistry(BaseModel):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=100, unique=True, db_index=True)  # e.g., "diabetes-cohort"
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "cymed_cohort_registries"
        ordering = ["name"]

    def __str__(self) -> str:
        return f"{self.name} ({self.code})"


class RegistryEntry(BaseModel):
    registry = models.ForeignKey(CohortRegistry, on_delete=models.CASCADE, related_name="entries")
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="registry_entries")
    joined_at = models.DateTimeField(default=timezone.now)
    status = models.CharField(
        max_length=30, choices=[("active", "Active"), ("inactive", "Inactive")], default="active"
    )

    class Meta:
        db_table = "cymed_registry_entries"
        unique_together = [("registry", "patient")]
