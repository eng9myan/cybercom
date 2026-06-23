"""
CyMed Pharmacy — Dispensing Module
Models: DispenseOrder, DispenseItem, DispenseBatch, DispenseVerification, DispenseAudit

Covers: Pharmacist Verification, Dispensing Workflow, Barcode Verification,
        Batch Verification, Medication Pickup
FHIR: MedicationDispense
"""
from django.db import models
from platform.common.models import BaseModel


class DispenseStatus(models.TextChoices):
    QUEUED = "queued", "Queued"
    IN_PROGRESS = "in_progress", "In Progress"
    VERIFICATION_PENDING = "verification_pending", "Pending Pharmacist Verification"
    VERIFIED = "verified", "Pharmacist Verified"
    READY = "ready", "Ready for Pickup"
    DISPENSED = "dispensed", "Dispensed"
    PARTIAL = "partial", "Partially Dispensed"
    RETURNED = "returned", "Returned"
    CANCELLED = "cancelled", "Cancelled"


class DispenseOrder(BaseModel):
    """
    Primary dispensing workflow record. Created from a verified prescription or medication order.
    Tracks the complete dispensing lifecycle from queue to patient pickup.
    FHIR: MedicationDispense
    """
    DISPENSE_TYPES = [
        ("retail", "Retail Dispense"),
        ("inpatient", "Inpatient / Unit Dose"),
        ("iv_admixture", "IV Admixture"),
        ("batch", "Batch Dispense"),
        ("emergency", "Emergency Dispense"),
    ]
    PICKUP_METHODS = [
        ("counter", "Counter Pickup"),
        ("bedside", "Bedside Delivery"),
        ("ward_cart", "Ward Medication Cart"),
        ("adc", "Automated Dispensing Cabinet"),
        ("robot", "Dispensing Robot"),
        ("mail", "Mail Order"),
        ("delivery", "Home Delivery"),
    ]

    dispense_number = models.CharField(max_length=100, unique=True, db_index=True)
    prescription_id = models.UUIDField(null=True, blank=True, db_index=True)
    medication_order_id = models.UUIDField(null=True, blank=True, db_index=True)
    patient_id = models.UUIDField(db_index=True)
    encounter_id = models.UUIDField(null=True, blank=True)
    admission_id = models.UUIDField(null=True, blank=True)

    dispense_type = models.CharField(max_length=30, choices=DISPENSE_TYPES, default="retail")
    status = models.CharField(
        max_length=30, choices=DispenseStatus.choices, default=DispenseStatus.QUEUED
    )
    pickup_method = models.CharField(max_length=30, choices=PICKUP_METHODS, default="counter")

    # Pharmacy assignment
    pharmacist_id = models.UUIDField(null=True, blank=True)           # Assigned pharmacist
    technician_id = models.UUIDField(null=True, blank=True)           # Assigned technician
    pharmacy_location = models.CharField(max_length=255, blank=True)
    dispensing_counter = models.CharField(max_length=50, blank=True)

    # Verification
    verified_by = models.UUIDField(null=True, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)

    # Dispensed
    dispensed_by = models.UUIDField(null=True, blank=True)
    dispensed_at = models.DateTimeField(null=True, blank=True)

    # Pickup
    picked_up_by = models.CharField(max_length=255, blank=True)
    pickup_id_verified = models.BooleanField(default=False)
    picked_up_at = models.DateTimeField(null=True, blank=True)

    # FHIR
    fhir_medication_dispense_id = models.CharField(max_length=255, blank=True)

    # Counseling provided
    counseling_provided = models.BooleanField(default=False)
    counseling_notes = models.TextField(blank=True)

    # Automation
    automation_device_id = models.UUIDField(null=True, blank=True)    # CyIntegrationHub device

    notes = models.TextField(blank=True)

    class Meta:
        db_table = "cymed_rx_dispense_orders"
        indexes = [
            models.Index(fields=["patient_id", "status"]),
            models.Index(fields=["tenant_id", "dispense_type", "status"]),
            models.Index(fields=["prescription_id"]),
            models.Index(fields=["medication_order_id"]),
        ]

    def __str__(self):
        return f"{self.dispense_number} ({self.get_status_display()})"


class DispenseItem(BaseModel):
    """Individual medication line dispensed within a DispenseOrder."""
    ITEM_STATUS = [
        ("pending", "Pending"),
        ("picked", "Picked"),
        ("barcode_verified", "Barcode Verified"),
        ("verified", "Pharmacist Verified"),
        ("dispensed", "Dispensed"),
        ("returned", "Returned"),
        ("substituted", "Substituted"),
    ]

    dispense_order = models.ForeignKey(
        DispenseOrder, on_delete=models.CASCADE, related_name="items"
    )
    # Drug identification
    drug_code = models.CharField(max_length=100, db_index=True)
    drug_name = models.CharField(max_length=500)
    ndc_code = models.CharField(max_length=50, blank=True)            # NDC barcode
    lot_number = models.CharField(max_length=100, blank=True)
    expiry_date = models.DateField(null=True, blank=True)

    # Quantities
    quantity_prescribed = models.DecimalField(max_digits=10, decimal_places=3)
    quantity_dispensed = models.DecimalField(max_digits=10, decimal_places=3)
    quantity_unit = models.CharField(max_length=50)
    days_supply = models.PositiveSmallIntegerField(default=0)

    # Substitution
    is_substituted = models.BooleanField(default=False)
    original_drug_code = models.CharField(max_length=100, blank=True)
    substitution_reason = models.CharField(max_length=255, blank=True)

    # Barcode verification
    barcode_verified = models.BooleanField(default=False)
    barcode_verified_by = models.UUIDField(null=True, blank=True)
    barcode_verified_at = models.DateTimeField(null=True, blank=True)

    status = models.CharField(max_length=30, choices=ITEM_STATUS, default="pending")

    # Location / storage bin
    storage_bin = models.CharField(max_length=100, blank=True)
    adc_pocket = models.CharField(max_length=100, blank=True)

    class Meta:
        db_table = "cymed_rx_dispense_items"
        indexes = [models.Index(fields=["dispense_order", "status"])]


class DispenseBatch(BaseModel):
    """
    Batch dispensing record — groups multiple DispenseOrders for ward distribution
    or ADC restocking. Used for inpatient unit-dose cassette filling.
    """
    BATCH_TYPES = [
        ("unit_dose", "Unit Dose Batch"),
        ("ward_distribution", "Ward Distribution"),
        ("adc_restock", "ADC Restock"),
        ("robot_fill", "Robot Fill"),
        ("emergency_kit", "Emergency Kit"),
    ]
    STATUS_CHOICES = [
        ("open", "Open"),
        ("in_progress", "In Progress"),
        ("verification_pending", "Pending Verification"),
        ("verified", "Verified"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]

    batch_number = models.CharField(max_length=100, unique=True)
    batch_type = models.CharField(max_length=30, choices=BATCH_TYPES, default="unit_dose")
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default="open")
    ward_id = models.UUIDField(null=True, blank=True)
    target_date = models.DateField(null=True, blank=True)
    prepared_by = models.UUIDField(null=True, blank=True)
    verified_by = models.UUIDField(null=True, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    dispense_orders = models.ManyToManyField(DispenseOrder, related_name="batches", blank=True)

    class Meta:
        db_table = "cymed_rx_dispense_batches"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Batch {self.batch_number}"


class DispenseVerification(BaseModel):
    """
    Pharmacist double-check verification record for high-risk medications.
    Independent of the primary dispense flow — captures dual-check workflows.
    """
    VERIFICATION_TYPES = [
        ("first_check", "First Check"),
        ("second_check", "Second Check (Dual Verify)"),
        ("final_check", "Final Check"),
        ("clinical_review", "Clinical Review"),
    ]
    RESULT_CHOICES = [
        ("pass", "Passed"),
        ("fail_corrected", "Failed — Corrected"),
        ("fail_rejected", "Failed — Rejected"),
    ]

    dispense_order = models.ForeignKey(
        DispenseOrder, on_delete=models.CASCADE, related_name="verifications"
    )
    dispense_item = models.ForeignKey(
        DispenseItem, on_delete=models.CASCADE, related_name="verifications",
        null=True, blank=True
    )
    verification_type = models.CharField(max_length=30, choices=VERIFICATION_TYPES)
    verified_by = models.UUIDField()
    verified_at = models.DateTimeField(auto_now_add=True)
    result = models.CharField(max_length=30, choices=RESULT_CHOICES, default="pass")
    discrepancy_noted = models.TextField(blank=True)
    corrective_action = models.TextField(blank=True)

    class Meta:
        db_table = "cymed_rx_dispense_verifications"
        ordering = ["-verified_at"]


class DispenseAudit(BaseModel):
    """
    Immutable audit log for all dispense-related state changes.
    Supports compliance, regulatory, and controlled substance monitoring.
    """
    ACTION_TYPES = [
        ("created", "Order Created"),
        ("assigned", "Assigned to Pharmacist"),
        ("picked", "Medication Picked"),
        ("barcode_scanned", "Barcode Scanned"),
        ("verified", "Pharmacist Verified"),
        ("dispensed", "Dispensed to Patient"),
        ("returned", "Medication Returned"),
        ("cancelled", "Cancelled"),
        ("override", "Override Applied"),
    ]

    dispense_order = models.ForeignKey(
        DispenseOrder, on_delete=models.CASCADE, related_name="audit_log"
    )
    action = models.CharField(max_length=30, choices=ACTION_TYPES)
    performed_by = models.UUIDField()
    performed_at = models.DateTimeField(auto_now_add=True)
    details = models.JSONField(default=dict)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True)
    is_override = models.BooleanField(default=False)
    override_reason = models.TextField(blank=True)

    class Meta:
        db_table = "cymed_rx_dispense_audit"
        ordering = ["-performed_at"]
        indexes = [
            models.Index(fields=["dispense_order", "action"]),
            models.Index(fields=["tenant_id", "performed_at"]),
        ]
