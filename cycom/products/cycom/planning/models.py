from django.db import models

from platform.common.models import BaseModel


class ShiftSlot(BaseModel):
    DEPARTMENT_CHOICES = [
        ("sales", "Sales"),
        ("warehouse", "Warehouse"),
        ("finance", "Finance"),
        ("it", "IT"),
    ]
    STATE_CHOICES = [
        ("draft", "Draft"),
        ("published", "Published"),
        ("confirmed", "Confirmed"),
    ]

    resource_name = models.CharField(max_length=255)
    role = models.CharField(max_length=255, blank=True)
    department = models.CharField(max_length=20, choices=DEPARTMENT_CHOICES, default="sales")
    start_datetime = models.DateTimeField(null=True, blank=True)
    end_datetime = models.DateTimeField(null=True, blank=True)
    state = models.CharField(max_length=20, choices=STATE_CHOICES, default="draft")
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "cycom_planning_shift_slots"
        ordering = ["start_datetime"]

    def __str__(self):
        return f"{self.resource_name} @ {self.start_datetime}"
