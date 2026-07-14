from django.db import models

from platform.common.models import BaseModel


class ProviderOrderRequest(BaseModel):
    ORDER_CATEGORY_CHOICES = [
        ("laboratory", "Laboratory"),
        ("imaging", "Imaging"),
        ("medication", "Medication"),
        ("procedure", "Procedure"),
        ("referral", "Referral"),
        ("nursing", "Nursing"),
        ("dietary", "Dietary"),
        ("respiratory", "Respiratory"),
        ("physical_therapy", "Physical Therapy"),
        ("other", "Other"),
    ]
    PRIORITY_CHOICES = [
        ("routine", "Routine"),
        ("urgent", "Urgent"),
        ("stat", "STAT"),
    ]
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("submitted", "Submitted"),
        ("acknowledged", "Acknowledged"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
        ("on_hold", "On Hold"),
    ]

    patient_id = models.UUIDField(db_index=True)
    cymed_encounter_id = models.UUIDField(null=True, blank=True)
    ordering_provider_id = models.UUIDField(db_index=True)
    ordering_provider_name = models.CharField(max_length=255)
    order_category = models.CharField(max_length=30, choices=ORDER_CATEGORY_CHOICES)
    order_type = models.CharField(max_length=100, blank=True)
    order_name = models.CharField(max_length=255)
    order_details = models.JSONField(default=dict)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default="routine")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    clinical_indication = models.TextField(blank=True)
    fhir_service_request_id = models.CharField(max_length=255, blank=True)
    fhir_medication_request_id = models.CharField(max_length=255, blank=True)
    cymed_lab_order_id = models.UUIDField(null=True, blank=True)
    cymed_imaging_order_id = models.UUIDField(null=True, blank=True)
    cymed_rx_id = models.UUIDField(null=True, blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "cymed_prov_order_requests"
        indexes = [
            models.Index(fields=["tenant_id", "patient_id", "order_category"]),
            models.Index(fields=["tenant_id", "ordering_provider_id", "status"]),
        ]

    def __str__(self):
        return f"{self.order_name} ({self.order_category}) — {self.status}"


class OrderModification(BaseModel):
    MODIFICATION_TYPE_CHOICES = [
        ("edit", "Edit"),
        ("cancel", "Cancel"),
        ("hold", "Hold"),
        ("resume", "Resume"),
        ("priority_change", "Priority Change"),
    ]

    order = models.ForeignKey(
        ProviderOrderRequest,
        on_delete=models.CASCADE,
        related_name="modifications",
    )
    modified_by_provider_id = models.UUIDField()
    modified_by_name = models.CharField(max_length=255)
    modification_type = models.CharField(max_length=30, choices=MODIFICATION_TYPE_CHOICES)
    previous_value = models.JSONField(default=dict)
    new_value = models.JSONField(default=dict)
    reason = models.TextField()
    is_applied = models.BooleanField(default=True)

    class Meta:
        db_table = "cymed_prov_order_modifications"

    def __str__(self):
        return f"{self.modification_type} by {self.modified_by_name} — order {self.order_id}"


class OrderStatusUpdate(BaseModel):
    order = models.ForeignKey(
        ProviderOrderRequest,
        on_delete=models.CASCADE,
        related_name="status_updates",
    )
    previous_status = models.CharField(max_length=30)
    new_status = models.CharField(max_length=30)
    updated_by_provider_id = models.UUIDField(null=True, blank=True)
    updated_by_name = models.CharField(max_length=255, blank=True)
    updated_by_system = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "cymed_prov_order_status_updates"

    def __str__(self):
        return f"{self.previous_status} → {self.new_status} — order {self.order_id}"


class OrderSet(BaseModel):
    ORDER_SET_TYPE_CHOICES = [
        ("admission", "Admission"),
        ("discharge", "Discharge"),
        ("procedure", "Procedure"),
        ("condition_specific", "Condition Specific"),
        ("custom", "Custom"),
    ]

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    specialty = models.CharField(max_length=100, blank=True)
    order_set_type = models.CharField(max_length=30, choices=ORDER_SET_TYPE_CHOICES)
    orders = models.JSONField(default=list)
    created_by_provider_id = models.UUIDField()
    is_shared = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    usage_count = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "cymed_prov_order_sets"

    def __str__(self):
        return f"{self.name} ({self.order_set_type})"
