from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from platform.common.models import BaseModel
from products.cycom.hr.models import Employee


class Appraisal(BaseModel):
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("in_review", "In Review"),
        ("completed", "Completed"),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="appraisals")
    reviewer_name = models.CharField(max_length=255, blank=True)
    period_start = models.DateField()
    period_end = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    rating = models.PositiveSmallIntegerField(
        null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    strengths = models.TextField(blank=True)
    areas_for_improvement = models.TextField(blank=True)
    goals_next_period = models.TextField(blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "cycom_appraisals"
        ordering = ["-period_end"]

    def __str__(self):
        return f"{self.employee} — {self.period_start} to {self.period_end}"
