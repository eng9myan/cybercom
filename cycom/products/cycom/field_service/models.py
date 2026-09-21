from datetime import timedelta

from django.db import models
from django.utils import timezone

from platform.common.models import BaseModel


class ServiceContract(BaseModel):
    """A recurring service agreement with a customer, guaranteeing a
    completion time (sla_hours) for tasks logged against it."""

    customer_name = models.CharField(max_length=255)
    contract_number = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    sla_hours = models.PositiveIntegerField(
        help_text="Hours from a task's scheduled_at to completion this contract guarantees."
    )
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "cycom_field_service_contracts"
        unique_together = [("tenant_id", "contract_number")]
        ordering = ["-start_date"]

    def __str__(self):
        return f"{self.contract_number} — {self.customer_name}"


class ServiceTask(BaseModel):
    STATUS_CHOICES = [
        ("scheduled", "Scheduled"),
        ("en_route", "En Route"),
        ("in_progress", "In Progress"),
        ("done", "Done"),
        ("cancelled", "Cancelled"),
    ]

    contract = models.ForeignKey(
        ServiceContract, on_delete=models.SET_NULL, null=True, blank=True, related_name="tasks"
    )
    customer_name = models.CharField(max_length=255)
    address = models.CharField(max_length=500, blank=True)
    technician = models.CharField(max_length=255, blank=True)
    scheduled_at = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="scheduled")
    worksheet_notes = models.TextField(blank=True)
    customer_signature = models.TextField(
        blank=True, help_text="Base64-encoded signature capture or signature reference."
    )
    sla_deadline = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "cycom_field_service_tasks"
        ordering = ["-scheduled_at"]

    def __str__(self):
        return f"{self.customer_name} — {self.status}"

    @property
    def is_breached(self):
        if not self.sla_deadline:
            return False
        end = self.completed_at or timezone.now()
        return end > self.sla_deadline

    def save(self, *args, **kwargs):
        if self._state.adding and self.contract_id and not self.sla_deadline and self.scheduled_at:
            self.sla_deadline = self.scheduled_at + timedelta(hours=self.contract.sla_hours)
        super().save(*args, **kwargs)
