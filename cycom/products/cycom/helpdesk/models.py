from django.db import models

from platform.common.models import BaseModel


class Ticket(BaseModel):
    PRIORITY = [("low", "Low"), ("normal", "Normal"), ("high", "High"), ("urgent", "Urgent")]
    STAGE = [("new", "New"), ("in_progress", "In Progress"), ("waiting", "Waiting"), ("solved", "Solved"), ("closed", "Closed")]

    number = models.CharField(max_length=100)
    subject = models.CharField(max_length=255)
    customer_name = models.CharField(max_length=255, blank=True)
    assignee = models.CharField(max_length=255, blank=True)
    team = models.CharField(max_length=100, blank=True)
    priority = models.CharField(max_length=10, choices=PRIORITY, default="normal")
    stage = models.CharField(max_length=20, choices=STAGE, default="new")
    description = models.TextField(blank=True)

    class Meta:
        db_table = "cycom_helpdesk_tickets"
        unique_together = [("tenant_id", "number")]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.number} — {self.subject}"
