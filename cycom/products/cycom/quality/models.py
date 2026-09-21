from django.db import models

from platform.common.models import BaseModel


class InspectionPlan(BaseModel):
    """A reusable checklist template — a checkpoint can optionally be
    created against one, copying its criteria in for per-criterion results."""

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    linked_model = models.CharField(
        max_length=100, blank=True, help_text="What kind of record this plan applies to, e.g. 'catalog.Product'."
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "cycom_quality_inspection_plans"
        ordering = ["name"]

    def __str__(self):
        return self.name


class InspectionPlanCriterion(BaseModel):
    plan = models.ForeignKey(InspectionPlan, on_delete=models.CASCADE, related_name="criteria")
    sequence = models.PositiveIntegerField(default=10)
    description = models.CharField(max_length=500)
    expected_value = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "cycom_quality_inspection_plan_criteria"
        ordering = ["sequence", "id"]

    def __str__(self):
        return self.description


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

    inspection_plan = models.ForeignKey(
        InspectionPlan, on_delete=models.SET_NULL, null=True, blank=True, related_name="checkpoints"
    )
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

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        super().save(*args, **kwargs)
        if is_new and self.inspection_plan_id and not self.criterion_results.exists():
            CheckpointCriterionResult.objects.bulk_create(
                CheckpointCriterionResult(
                    tenant_id=self.tenant_id, checkpoint=self, criterion=criterion
                )
                for criterion in self.inspection_plan.criteria.all()
            )


class CheckpointCriterionResult(BaseModel):
    checkpoint = models.ForeignKey(
        QualityCheckpoint, on_delete=models.CASCADE, related_name="criterion_results"
    )
    criterion = models.ForeignKey(InspectionPlanCriterion, on_delete=models.PROTECT, related_name="+")
    passed = models.BooleanField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "cycom_quality_checkpoint_criterion_results"
        ordering = ["criterion__sequence"]
        unique_together = [("checkpoint", "criterion")]


class NonConformance(BaseModel):
    """Opened automatically whenever a checkpoint is recorded as failed —
    a failed inspection with no tracked corrective action is exactly the
    gap this closes."""

    STATUS_CHOICES = [
        ("open", "Open"),
        ("investigating", "Investigating"),
        ("corrective_action", "Corrective Action"),
        ("closed", "Closed"),
    ]
    DISPOSITION_CHOICES = [
        ("reject", "Reject"),
        ("rework", "Rework"),
        ("use_as_is", "Use As Is"),
        ("return_to_vendor", "Return to Vendor"),
    ]

    checkpoint = models.ForeignKey(
        QualityCheckpoint, on_delete=models.CASCADE, related_name="non_conformances"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="open")
    root_cause = models.TextField(blank=True)
    corrective_action = models.TextField(blank=True)
    disposition = models.CharField(max_length=20, choices=DISPOSITION_CHOICES, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "cycom_quality_non_conformances"
        ordering = ["-created_at"]

    def __str__(self):
        return f"NCR on {self.checkpoint} ({self.status})"
