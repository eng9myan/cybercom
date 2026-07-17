from django.db import models

from platform.common.models import BaseModel


class Lead(BaseModel):
    STAGE_CHOICES = [
        ("new", "New"),
        ("contacted", "Contacted"),
        ("qualified", "Qualified"),
        ("proposal", "Proposal"),
        ("won", "Won"),
        ("lost", "Lost"),
    ]

    name = models.CharField(max_length=255)
    contact_name = models.CharField(max_length=255, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    source = models.CharField(max_length=100, blank=True)
    stage = models.CharField(max_length=20, choices=STAGE_CHOICES, default="new")
    probability = models.DecimalField(max_digits=5, decimal_places=2, default=10)
    estimated_value = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    currency = models.CharField(max_length=10, default="JOD")
    expected_close_date = models.DateField(null=True, blank=True)
    assigned_to = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "cycom_crm_leads"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.stage})"
