from django.db import models

from platform.common.models import BaseModel


class ServiceTask(BaseModel):
    STATUS_CHOICES = [
        ("scheduled", "Scheduled"),
        ("en_route", "En Route"),
        ("in_progress", "In Progress"),
        ("done", "Done"),
        ("cancelled", "Cancelled"),
    ]

    customer_name = models.CharField(max_length=255)
    address = models.CharField(max_length=500, blank=True)
    technician = models.CharField(max_length=255, blank=True)
    scheduled_at = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="scheduled")
    worksheet_notes = models.TextField(blank=True)
    customer_signature = models.TextField(
        blank=True, help_text="Base64-encoded signature capture or signature reference."
    )
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "cycom_field_service_tasks"
        ordering = ["-scheduled_at"]

    def __str__(self):
        return f"{self.customer_name} — {self.status}"
