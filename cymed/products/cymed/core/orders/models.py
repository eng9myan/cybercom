from django.db import models
from django.utils import timezone

from platform.common.models import BaseModel
from products.cymed.core.encounters.models import Encounter
from products.cymed.core.patients.models import Patient


class OrderType(models.TextChoices):
    LABORATORY = "laboratory", "Laboratory Order"
    IMAGING = "imaging", "Imaging Order"
    MEDICATION = "medication", "Medication Request"
    PROCEDURE = "procedure", "Procedure Request"
    REFERRAL = "referral", "Referral Request"


class OrderPriority(models.TextChoices):
    ROUTINE = "routine", "Routine"
    URGENT = "urgent", "Urgent"
    STAT = "stat", "STAT (Immediate)"


class OrderStatus(models.TextChoices):
    PROPOSED = "proposed", "Proposed"
    DRAFT = "draft", "Draft"
    ACTIVE = "active", "Active"
    COMPLETED = "completed", "Completed"
    CANCELLED = "cancelled", "Cancelled"


class Order(BaseModel):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="orders")
    encounter = models.ForeignKey(
        Encounter, on_delete=models.SET_NULL, null=True, blank=True, related_name="orders"
    )
    order_type = models.CharField(max_length=30, choices=OrderType.choices)
    priority = models.CharField(
        max_length=20, choices=OrderPriority.choices, default=OrderPriority.ROUTINE
    )
    status = models.CharField(max_length=30, choices=OrderStatus.choices, default=OrderStatus.DRAFT)
    ordered_by = models.CharField(max_length=255)
    ordered_at = models.DateTimeField(default=timezone.now)
    # CyID ecosystem, Phase 5 — `tenant_id` (BaseModel) is the SOURCE
    # tenant (who wrote the order, e.g. a clinic). This is the FULFILLING
    # tenant (who executes it, e.g. an external pharmacy or lab) when it
    # differs — null means "fulfilled within the source tenant," the
    # original, unchanged behavior. Same raw-UUID-not-FK convention as
    # Consent.granted_to_tenant_id (see core/consents/models.py) — a
    # cross-tenant reference, not a same-database FK.
    fulfilling_tenant_id = models.UUIDField(null=True, blank=True, db_index=True)

    class Meta:
        db_table = "cymed_orders"
        ordering = ["-ordered_at"]

    def __str__(self) -> str:
        return f"Order({self.order_type}, {self.status}, {self.patient.mrn})"


class OrderItem(BaseModel):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    code = models.CharField(max_length=100)  # LOINC, RxNorm, or SNOMED
    display = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        db_table = "cymed_order_items"


class OrderResult(BaseModel):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="results")
    result_text = models.TextField()
    result_reference_id = models.UUIDField(
        null=True, blank=True
    )  # maps to Observation or diagnostic report
    recorded_at = models.DateTimeField(default=timezone.now)
    recorded_by = models.CharField(max_length=255)

    class Meta:
        db_table = "cymed_order_results"
