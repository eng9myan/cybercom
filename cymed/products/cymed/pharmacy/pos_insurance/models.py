"""CyMed Pharmacy pos_insurance models."""
from __future__ import annotations

import uuid
from decimal import Decimal

from django.db import models
from django.utils import timezone

from platform.common.models import BaseModel


class PosTerminal(BaseModel):
    tenant_id = models.UUIDField(db_index=True)
    code = models.CharField(max_length=64)
    facility_id = models.UUIDField(null=True, blank=True)
    location_label = models.CharField(max_length=128, blank=True)
    active = models.BooleanField(default=True)
    last_seen_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "cymed_pharmacy_pos_insurance_pos_terminal"
        unique_together = [("tenant_id", "code")]

    def __str__(self) -> str:
        return f"PosTerminal({self.code})"


class PosSession(BaseModel):
    class Status(models.TextChoices):
        OPEN = "open", "Open"
        CLOSED = "closed", "Closed"
        RECONCILED = "reconciled", "Reconciled"

    tenant_id = models.UUIDField(db_index=True)
    terminal = models.ForeignKey(PosTerminal, on_delete=models.CASCADE, related_name="sessions")
    cashier_profile_id = models.UUIDField(null=True, blank=True)
    started_at = models.DateTimeField(default=timezone.now)
    ended_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.OPEN)
    opening_float = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))
    closing_cash = models.DecimalField(max_digits=18, decimal_places=4, null=True, blank=True)

    class Meta:
        db_table = "cymed_pharmacy_pos_insurance_pos_session"

    def __str__(self) -> str:
        return f"PosSession({self.pk}, {self.status})"


class PosSale(BaseModel):
    class AdjudicationStatus(models.TextChoices):
        NOT_REQUIRED = "not_required", "Not Required"
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        PARTIAL = "partial", "Partial"

    tenant_id = models.UUIDField(db_index=True)
    session = models.ForeignKey(PosSession, on_delete=models.CASCADE, related_name="sales")
    patient_profile_id = models.UUIDField(null=True, blank=True)
    order_id = models.UUIDField(null=True, blank=True)
    insurance_used = models.BooleanField(default=False)
    insurance_policy_id = models.UUIDField(null=True, blank=True)
    total_gross = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))
    insurance_covered = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))
    patient_share = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))
    adjudication_status = models.CharField(
        max_length=32,
        choices=AdjudicationStatus.choices,
        default=AdjudicationStatus.NOT_REQUIRED,
    )
    adjudication_reference = models.CharField(max_length=128, blank=True)
    adjudication_response = models.JSONField(default=dict, blank=True)
    payment_ref = models.CharField(max_length=128, blank=True)

    class Meta:
        db_table = "cymed_pharmacy_pos_insurance_pos_sale"

    def __str__(self) -> str:
        return f"PosSale({self.pk}, {self.adjudication_status})"


class PosSaleItem(BaseModel):
    sale = models.ForeignKey(PosSale, on_delete=models.CASCADE, related_name="items")
    product_id = models.UUIDField()
    product_name = models.CharField(max_length=255)
    qty = models.IntegerField(default=1)
    unit_price = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))
    line_total = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))
    is_covered = models.BooleanField(default=False)
    coverage_amount = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0"))

    class Meta:
        db_table = "cymed_pharmacy_pos_insurance_pos_sale_item"

    def __str__(self) -> str:
        return f"PosSaleItem({self.product_name} x{self.qty})"


class AdjudicationLog(BaseModel):
    class Payer(models.TextChoices):
        NPHIES = "nphies", "NPHIES"
        JOFOTARA = "jofotara", "JoFotara"
        DIRECT = "direct", "Direct"
        MANUAL = "manual", "Manual"

    sale = models.ForeignKey(PosSale, on_delete=models.CASCADE, related_name="adjudication_logs")
    at = models.DateTimeField(default=timezone.now)
    payer = models.CharField(max_length=32, choices=Payer.choices, default=Payer.NPHIES)
    request_payload = models.JSONField(default=dict, blank=True)
    response_payload = models.JSONField(default=dict, blank=True)
    latency_ms = models.IntegerField(default=0)
    ok = models.BooleanField(default=False)
    error_message = models.TextField(blank=True)

    class Meta:
        db_table = "cymed_pharmacy_pos_insurance_adjudication_log"

    def __str__(self) -> str:
        return f"AdjudicationLog(sale={self.sale_id}, ok={self.ok})"
