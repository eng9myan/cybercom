"""
CyMed Pharmacy — Procurement Bridge (CyCom ERP Integration)
CyCom ERP owns procurement. This bridge creates procurement requests
and queries supplier status via CyIntegrationHub.
NO ERP procurement logic inside pharmacy.
"""

from django.db import models

from platform.common.models import BaseModel


class ProcurementRequest(BaseModel):
    """
    Pharmacy-initiated procurement request, forwarded to CyCom ERP via event.
    Published as 'cymed.procurement.requested' for CyCom ERP processing.
    """

    REQUEST_TYPES = [
        ("reorder", "Routine Reorder"),
        ("emergency", "Emergency Procurement"),
        ("non_formulary", "Non-Formulary Request"),
        ("shortage", "Drug Shortage"),
    ]
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("submitted", "Submitted to ERP"),
        ("approved", "ERP Approved"),
        ("ordered", "Purchase Order Created"),
        ("received", "Received"),
        ("cancelled", "Cancelled"),
    ]

    request_number = models.CharField(max_length=100, unique=True, db_index=True)
    request_type = models.CharField(max_length=30, choices=REQUEST_TYPES, default="reorder")
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default="draft")
    drug_code = models.CharField(max_length=100, db_index=True)
    drug_name = models.CharField(max_length=500)
    quantity_requested = models.DecimalField(max_digits=12, decimal_places=3)
    quantity_unit = models.CharField(max_length=50)
    urgency = models.CharField(
        max_length=20,
        choices=[("routine", "Routine"), ("urgent", "Urgent"), ("emergency", "Emergency")],
        default="routine",
    )
    clinical_justification = models.TextField(blank=True)
    requested_by = models.UUIDField()
    preferred_supplier_id = models.CharField(max_length=255, blank=True)  # CyCom ERP supplier
    target_delivery_date = models.DateField(null=True, blank=True)

    # ERP tracking
    erp_purchase_order_id = models.CharField(max_length=255, blank=True)
    erp_submitted_at = models.DateTimeField(null=True, blank=True)
    erp_response = models.JSONField(default=dict)

    notes = models.TextField(blank=True)

    class Meta:
        db_table = "cymed_procurement_requests"
        indexes = [
            models.Index(fields=["tenant_id", "status", "urgency"]),
            models.Index(fields=["drug_code", "request_type"]),
        ]

    def __str__(self):
        return f"{self.request_number} — {self.drug_name}"
