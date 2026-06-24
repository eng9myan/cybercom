import uuid
from django.db import models
from platform.common.models import BaseModel


class Charge(BaseModel):
    """
    A single billable charge generated from a clinical event.
    Sourced from orders, procedures, admissions, or pharmacy dispenses.
    """

    SERVICE_SOURCE_CHOICES = [
        ("clinic", "Clinic"),
        ("hospital", "Hospital"),
        ("laboratory", "Laboratory"),
        ("imaging", "Imaging"),
        ("pharmacy", "Pharmacy"),
        ("emergency", "Emergency"),
        ("or", "Operating Room"),
        ("icu", "ICU"),
    ]

    CHARGE_CATEGORY_CHOICES = [
        ("consultation", "Consultation"),
        ("procedure", "Procedure"),
        ("medication", "Medication"),
        ("lab_test", "Lab Test"),
        ("imaging", "Imaging"),
        ("admission", "Admission"),
        ("room_and_board", "Room and Board"),
        ("nursing", "Nursing"),
        ("anesthesia", "Anesthesia"),
        ("therapy", "Therapy"),
        ("supply", "Supply"),
        ("other", "Other"),
    ]

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("reviewed", "Reviewed"),
        ("approved", "Approved"),
        ("billed", "Billed"),
        ("voided", "Voided"),
    ]

    patient_id = models.UUIDField(db_index=True)
    encounter_id = models.UUIDField(db_index=True)
    charge_date = models.DateField()
    service_source = models.CharField(max_length=20, choices=SERVICE_SOURCE_CHOICES)
    charge_category = models.CharField(max_length=30, choices=CHARGE_CATEGORY_CHOICES)
    service_code = models.CharField(max_length=50)
    service_description = models.CharField(max_length=500)
    icd11_diagnosis_code = models.CharField(max_length=20, blank=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    is_billable = models.BooleanField(default=True)
    source_order_id = models.UUIDField(null=True, blank=True)
    source_module = models.CharField(max_length=50, blank=True)
    rendering_provider_id = models.UUIDField(null=True, blank=True)
    facility_id = models.UUIDField(db_index=True)
    encounter_billing_id = models.UUIDField(null=True, blank=True)

    class Meta:
        db_table = "cymed_rcm_chg_charges"
        ordering = ["-charge_date"]

    def __str__(self):
        return f"Charge {self.service_code} ({self.status}) - {self.charge_date}"


class ChargeItem(BaseModel):
    """
    Sub-component or supply item contributing to a parent charge.
    Tracks individual unit costs that roll up to the charge total.
    """

    charge = models.ForeignKey(
        Charge,
        on_delete=models.CASCADE,
        related_name="items",
    )
    item_code = models.CharField(max_length=50)
    item_description = models.CharField(max_length=500)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        db_table = "cymed_rcm_chg_charge_items"
        ordering = ["created_at"]

    def __str__(self):
        return f"ChargeItem {self.item_code} on Charge {self.charge_id}"


class ChargeRule(BaseModel):
    """
    Automation rule that triggers charge generation on clinical events.
    Maps trigger events to service codes and configures multipliers.
    """

    SERVICE_SOURCE_CHOICES = [
        ("clinic", "Clinic"),
        ("hospital", "Hospital"),
        ("laboratory", "Laboratory"),
        ("imaging", "Imaging"),
        ("pharmacy", "Pharmacy"),
        ("emergency", "Emergency"),
        ("or", "Operating Room"),
        ("icu", "ICU"),
    ]

    CHARGE_CATEGORY_CHOICES = [
        ("consultation", "Consultation"),
        ("procedure", "Procedure"),
        ("medication", "Medication"),
        ("lab_test", "Lab Test"),
        ("imaging", "Imaging"),
        ("admission", "Admission"),
        ("room_and_board", "Room and Board"),
        ("nursing", "Nursing"),
        ("anesthesia", "Anesthesia"),
        ("therapy", "Therapy"),
        ("supply", "Supply"),
        ("other", "Other"),
    ]

    rule_name = models.CharField(max_length=200)
    service_source = models.CharField(max_length=20, choices=SERVICE_SOURCE_CHOICES)
    charge_category = models.CharField(max_length=30, choices=CHARGE_CATEGORY_CHOICES)
    auto_generate = models.BooleanField(default=True)
    trigger_event = models.CharField(max_length=50)
    service_code_map = models.JSONField(default=dict)
    multiplier = models.DecimalField(max_digits=8, decimal_places=4, default=1)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "cymed_rcm_chg_charge_rules"
        ordering = ["rule_name"]

    def __str__(self):
        return f"ChargeRule '{self.rule_name}' ({self.service_source})"


class ChargeAdjustment(BaseModel):
    """
    Adjustment applied to a charge before billing (discount, override, correction, etc.).
    """

    ADJUSTMENT_TYPE_CHOICES = [
        ("discount", "Discount"),
        ("correction", "Correction"),
        ("override", "Override"),
        ("void", "Void"),
        ("split", "Split"),
    ]

    charge = models.ForeignKey(
        Charge,
        on_delete=models.CASCADE,
        related_name="adjustments",
    )
    adjustment_type = models.CharField(max_length=30, choices=ADJUSTMENT_TYPE_CHOICES)
    original_amount = models.DecimalField(max_digits=12, decimal_places=2)
    adjusted_amount = models.DecimalField(max_digits=12, decimal_places=2)
    reason = models.TextField(blank=True)
    adjusted_by_user_id = models.UUIDField()

    class Meta:
        db_table = "cymed_rcm_chg_adjustments"
        ordering = ["-created_at"]

    def __str__(self):
        return f"ChargeAdjustment {self.adjustment_type} on Charge {self.charge_id}"


class ChargeAudit(BaseModel):
    """
    Immutable audit log of all status changes and actions performed on a charge.
    """

    ACTION_CHOICES = [
        ("created", "Created"),
        ("modified", "Modified"),
        ("approved", "Approved"),
        ("voided", "Voided"),
        ("billed", "Billed"),
        ("reversed", "Reversed"),
    ]

    charge = models.ForeignKey(
        Charge,
        on_delete=models.CASCADE,
        related_name="audits",
    )
    action = models.CharField(max_length=30, choices=ACTION_CHOICES)
    performed_by_user_id = models.UUIDField()
    previous_status = models.CharField(max_length=20, blank=True)
    new_status = models.CharField(max_length=20, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "cymed_rcm_chg_audits"
        ordering = ["-created_at"]

    def __str__(self):
        return f"ChargeAudit {self.action} on Charge {self.charge_id}"
