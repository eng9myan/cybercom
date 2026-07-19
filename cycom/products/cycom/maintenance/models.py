from django.db import models

from platform.common.models import BaseModel
from products.cycom.inventory.models import Warehouse


class Equipment(BaseModel):
    name = models.CharField(max_length=255)
    serial_number = models.CharField(max_length=100, blank=True)
    warehouse = models.ForeignKey(
        Warehouse, on_delete=models.PROTECT, related_name="equipment", null=True, blank=True
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "cycom_maintenance_equipment"
        ordering = ["name"]

    def __str__(self):
        return self.name


class MaintenanceRequest(BaseModel):
    TYPE_CHOICES = [("preventive", "Preventive"), ("corrective", "Corrective")]
    STATUS_CHOICES = [
        ("scheduled", "Scheduled"),
        ("in_progress", "In Progress"),
        ("done", "Done"),
        ("cancelled", "Cancelled"),
    ]

    equipment = models.ForeignKey(Equipment, on_delete=models.PROTECT, related_name="requests")
    request_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default="corrective")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="scheduled")
    description = models.TextField(blank=True)
    technician = models.CharField(max_length=255, blank=True)
    scheduled_date = models.DateField()
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    downtime_hours = models.DecimalField(max_digits=8, decimal_places=2, default=0)

    class Meta:
        db_table = "cycom_maintenance_requests"
        ordering = ["-scheduled_date"]

    def __str__(self):
        return f"{self.equipment} — {self.request_type} ({self.status})"
