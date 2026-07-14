"""
CyMed Pharmacy — Prescription Management
Models: Prescription, PrescriptionItem, MedicationOrder, MedicationOrderStatus,
        MedicationRenewal, MedicationRefill, PrescriptionAttachment

FHIR: MedicationRequest, MedicationDispense
Terminology: Medication codes via TerminologyService (no local drug store duplication).
Controlled substance tracking with DEA schedule awareness.
"""

from django.db import models

from platform.common.models import BaseModel


class PrescriptionType(models.TextChoices):
    OUTPATIENT = "outpatient", "Outpatient"
    INPATIENT = "inpatient", "Inpatient"
    EMERGENCY = "emergency", "Emergency"
    DISCHARGE = "discharge", "Discharge"
    CONTROLLED = "controlled", "Controlled Substance"
    STANDING = "standing", "Standing Order"
    REFILL = "refill", "Refill"


class PrescriptionStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    PENDING = "pending", "Pending Verification"
    ACTIVE = "active", "Active"
    DISPENSED = "dispensed", "Dispensed"
    COMPLETED = "completed", "Completed"
    CANCELLED = "cancelled", "Cancelled"
    ON_HOLD = "on_hold", "On Hold"
    EXPIRED = "expired", "Expired"
    REJECTED = "rejected", "Rejected"


class MedicationPriority(models.TextChoices):
    STAT = "stat", "STAT"
    URGENT = "urgent", "Urgent"
    ROUTINE = "routine", "Routine"


class DEASchedule(models.TextChoices):
    SCHEDULE_I = "I", "Schedule I"
    SCHEDULE_II = "II", "Schedule II"
    SCHEDULE_III = "III", "Schedule III"
    SCHEDULE_IV = "IV", "Schedule IV"
    SCHEDULE_V = "V", "Schedule V"
    NON_CONTROLLED = "none", "Non-Controlled"


class Prescription(BaseModel):
    """
    Core prescription record. Supports electronic, paper, verbal, and telephone prescriptions.
    Linked to FHIR MedicationRequest. Controlled substance tracking via DEA schedule.
    Medication codes resolved via TerminologyService — no local drug database duplication.
    """

    prescription_number = models.CharField(max_length=100, unique=True, db_index=True)
    patient_id = models.UUIDField(db_index=True)  # CyMed Core patient
    encounter_id = models.UUIDField(null=True, blank=True, db_index=True)
    admission_id = models.UUIDField(null=True, blank=True)  # Hospital inpatient
    prescriber_id = models.UUIDField(db_index=True)  # CyIdentity provider
    prescriber_npi = models.CharField(max_length=20, blank=True)
    prescriber_dea = models.CharField(max_length=20, blank=True)  # For controlled Rx
    dispensing_pharmacy_id = models.UUIDField(null=True, blank=True)
    prescription_type = models.CharField(
        max_length=30, choices=PrescriptionType.choices, default=PrescriptionType.OUTPATIENT
    )
    status = models.CharField(
        max_length=30, choices=PrescriptionStatus.choices, default=PrescriptionStatus.PENDING
    )
    priority = models.CharField(
        max_length=20, choices=MedicationPriority.choices, default=MedicationPriority.ROUTINE
    )

    # FHIR linking
    fhir_medication_request_id = models.CharField(max_length=255, blank=True, db_index=True)

    # Clinical context
    diagnosis_codes = models.JSONField(default=list)  # ICD-11 codes from TerminologyService
    clinical_notes = models.TextField(blank=True)
    allergy_override = models.BooleanField(default=False)
    allergy_override_reason = models.TextField(blank=True)
    interaction_override = models.BooleanField(default=False)
    interaction_override_reason = models.TextField(blank=True)

    # Dates
    prescribed_at = models.DateTimeField(auto_now_add=True)
    valid_from = models.DateField(null=True, blank=True)
    valid_until = models.DateField(null=True, blank=True)
    dispensed_at = models.DateTimeField(null=True, blank=True)

    # Pharmacy verification
    verified_by = models.UUIDField(null=True, blank=True)  # Pharmacist
    verified_at = models.DateTimeField(null=True, blank=True)

    # Controlled substance
    is_controlled = models.BooleanField(default=False, db_index=True)
    dea_schedule = models.CharField(
        max_length=10, choices=DEASchedule.choices, default=DEASchedule.NON_CONTROLLED
    )

    # Refill
    refills_authorized = models.PositiveSmallIntegerField(default=0)
    refills_dispensed = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = "cymed_rx_prescriptions"
        indexes = [
            models.Index(fields=["patient_id", "status"]),
            models.Index(fields=["tenant_id", "prescription_type", "status"]),
            models.Index(fields=["prescriber_id", "prescribed_at"]),
            models.Index(fields=["is_controlled", "dea_schedule"]),
        ]

    def __str__(self):
        return f"{self.prescription_number} ({self.get_status_display()})"

    @property
    def can_refill(self):
        return (
            self.status in (PrescriptionStatus.ACTIVE, PrescriptionStatus.DISPENSED)
            and self.refills_dispensed < self.refills_authorized
        )


class PrescriptionItem(BaseModel):
    """
    Individual medication line within a prescription.
    Drug codes resolved via TerminologyService (RxNorm, SNOMED).
    """

    prescription = models.ForeignKey(Prescription, on_delete=models.CASCADE, related_name="items")
    # Drug identification — resolved via TerminologyService
    drug_code = models.CharField(max_length=100, db_index=True)  # RxNorm CUI
    drug_name = models.CharField(max_length=500)
    drug_name_ar = models.CharField(max_length=500, blank=True)
    snomed_code = models.CharField(max_length=50, blank=True)
    generic_code = models.CharField(max_length=100, blank=True)  # Generic RxNorm

    # Dosage
    dose = models.CharField(max_length=100)
    dose_unit = models.CharField(max_length=50)
    route = models.CharField(max_length=100)  # Oral, IV, IM, etc.
    frequency = models.CharField(max_length=100)  # TID, BID, PRN, etc.
    duration = models.CharField(max_length=100, blank=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=3)
    quantity_unit = models.CharField(max_length=50)
    days_supply = models.PositiveSmallIntegerField(default=0)

    # Substitution
    dispense_as_written = models.BooleanField(default=False)  # DAW flag
    substitution_allowed = models.BooleanField(default=True)

    # Instructions
    sig = models.TextField()  # Patient instructions
    pharmacist_notes = models.TextField(blank=True)
    special_instructions = models.TextField(blank=True)

    # Status
    is_active = models.BooleanField(default=True)
    cancelled_reason = models.TextField(blank=True)

    class Meta:
        db_table = "cymed_rx_prescription_items"
        indexes = [models.Index(fields=["prescription", "drug_code"])]

    def __str__(self):
        return f"{self.drug_name} {self.dose}{self.dose_unit}"


class MedicationOrder(BaseModel):
    """
    Hospital medication order (inpatient MAR-linked).
    Separate from retail prescriptions — supports unit dose, IV admixture, PRN.
    """

    ORDER_TYPES = [
        ("scheduled", "Scheduled"),
        ("prn", "PRN (As Needed)"),
        ("one_time", "One Time"),
        ("stat", "STAT"),
        ("continuous", "Continuous Infusion"),
        ("unit_dose", "Unit Dose"),
        ("iv_admixture", "IV Admixture"),
    ]
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("pending_verification", "Pending Verification"),
        ("verified", "Pharmacist Verified"),
        ("active", "Active"),
        ("on_hold", "On Hold"),
        ("discontinued", "Discontinued"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]

    order_number = models.CharField(max_length=100, unique=True, db_index=True)
    patient_id = models.UUIDField(db_index=True)
    admission_id = models.UUIDField(db_index=True)
    encounter_id = models.UUIDField(null=True, blank=True)
    ward_id = models.UUIDField(null=True, blank=True)
    bed_id = models.CharField(max_length=50, blank=True)
    prescriber_id = models.UUIDField(db_index=True)

    order_type = models.CharField(max_length=30, choices=ORDER_TYPES, default="scheduled")
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default="pending_verification")
    priority = models.CharField(
        max_length=20, choices=MedicationPriority.choices, default=MedicationPriority.ROUTINE
    )

    # Drug — via TerminologyService
    drug_code = models.CharField(max_length=100, db_index=True)
    drug_name = models.CharField(max_length=500)
    dose = models.CharField(max_length=100)
    dose_unit = models.CharField(max_length=50)
    route = models.CharField(max_length=100)
    frequency = models.CharField(max_length=100)
    start_date = models.DateField(null=True, blank=True)
    stop_date = models.DateField(null=True, blank=True)
    duration_days = models.PositiveSmallIntegerField(default=0)

    # Pharmacist verification
    verified_by = models.UUIDField(null=True, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    pharmacy_notes = models.TextField(blank=True)

    # FHIR
    fhir_medication_request_id = models.CharField(max_length=255, blank=True)

    # Controlled
    is_controlled = models.BooleanField(default=False)
    dea_schedule = models.CharField(
        max_length=10, choices=DEASchedule.choices, default=DEASchedule.NON_CONTROLLED
    )

    class Meta:
        db_table = "cymed_rx_medication_orders"
        indexes = [
            models.Index(fields=["patient_id", "admission_id", "status"]),
            models.Index(fields=["tenant_id", "order_type", "status"]),
            models.Index(fields=["ward_id", "status"]),
        ]

    def __str__(self):
        return f"{self.order_number} — {self.drug_name}"


class MedicationOrderStatus(BaseModel):
    """Immutable status history for medication orders."""

    order = models.ForeignKey(
        MedicationOrder, on_delete=models.CASCADE, related_name="status_history"
    )
    from_status = models.CharField(max_length=30)
    to_status = models.CharField(max_length=30)
    changed_by = models.UUIDField(null=True, blank=True)
    reason = models.CharField(max_length=500, blank=True)
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "cymed_rx_medication_order_status"
        ordering = ["-changed_at"]


class MedicationRenewal(BaseModel):
    """
    Prescription renewal request — extends an existing prescription.
    Requires pharmacist review and prescriber authorization.
    """

    STATUS_CHOICES = [
        ("requested", "Renewal Requested"),
        ("under_review", "Under Pharmacist Review"),
        ("pending_prescriber", "Pending Prescriber Authorization"),
        ("authorized", "Authorized"),
        ("denied", "Denied"),
        ("expired", "Expired"),
    ]

    prescription = models.ForeignKey(
        Prescription, on_delete=models.CASCADE, related_name="renewals"
    )
    requested_by = models.UUIDField()  # Patient or authorized staff
    requested_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default="requested")
    renewal_duration_days = models.PositiveSmallIntegerField(default=30)
    clinical_justification = models.TextField(blank=True)
    reviewed_by = models.UUIDField(null=True, blank=True)  # Pharmacist
    reviewed_at = models.DateTimeField(null=True, blank=True)
    authorized_by = models.UUIDField(null=True, blank=True)  # Prescriber
    authorized_at = models.DateTimeField(null=True, blank=True)
    denial_reason = models.TextField(blank=True)

    class Meta:
        db_table = "cymed_rx_medication_renewals"
        ordering = ["-requested_at"]


class MedicationRefill(BaseModel):
    """Tracks each physical refill event for a prescription."""

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("ready", "Ready for Pickup"),
        ("dispensed", "Dispensed"),
        ("cancelled", "Cancelled"),
    ]

    prescription = models.ForeignKey(Prescription, on_delete=models.CASCADE, related_name="refills")
    refill_number = models.PositiveSmallIntegerField()
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default="pending")
    requested_at = models.DateTimeField(auto_now_add=True)
    dispensed_at = models.DateTimeField(null=True, blank=True)
    dispensed_by = models.UUIDField(null=True, blank=True)
    quantity_dispensed = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    days_supply = models.PositiveSmallIntegerField(default=0)
    pickup_method = models.CharField(
        max_length=30,
        choices=[("counter", "Counter Pickup"), ("delivery", "Delivery"), ("mail", "Mail")],
        default="counter",
    )
    picked_up_by = models.CharField(max_length=255, blank=True)  # Patient name or authorized person
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "cymed_rx_medication_refills"
        indexes = [models.Index(fields=["prescription", "refill_number"])]
        unique_together = [("prescription", "refill_number")]


class PrescriptionAttachment(BaseModel):
    """
    Documents attached to a prescription (handwritten scan, prior auth, patient ID).
    File content stored via CyData — URL reference only.
    """

    ATTACHMENT_TYPES = [
        ("handwritten_rx", "Handwritten Prescription Scan"),
        ("prior_auth", "Prior Authorization"),
        ("patient_id", "Patient Identification"),
        ("insurance_card", "Insurance Card"),
        ("referral", "Referral Letter"),
        ("lab_result", "Supporting Lab Result"),
        ("other", "Other"),
    ]

    prescription = models.ForeignKey(
        Prescription, on_delete=models.CASCADE, related_name="attachments"
    )
    attachment_type = models.CharField(max_length=30, choices=ATTACHMENT_TYPES, default="other")
    file_name = models.CharField(max_length=255)
    file_type = models.CharField(max_length=50)
    file_url = models.URLField(max_length=2000)
    file_size_bytes = models.PositiveBigIntegerField(default=0)
    uploaded_by = models.UUIDField()
    description = models.CharField(max_length=500, blank=True)

    class Meta:
        db_table = "cymed_rx_prescription_attachments"


class MedicationHistory(BaseModel):
    """
    Longitudinal medication history per patient (across all encounters and refills).
    Populated from dispensing, admissions, and patient-reported medications.
    """

    SOURCE_CHOICES = [
        ("prescription", "Prescription Dispensed"),
        ("admission", "Admission Reconciliation"),
        ("patient_reported", "Patient Reported"),
        ("transfer", "Transfer Record"),
        ("discharge", "Discharge Record"),
        ("external", "External Record"),
    ]

    patient_id = models.UUIDField(db_index=True)
    drug_code = models.CharField(max_length=100, db_index=True)
    drug_name = models.CharField(max_length=500)
    dose = models.CharField(max_length=100, blank=True)
    dose_unit = models.CharField(max_length=50, blank=True)
    route = models.CharField(max_length=100, blank=True)
    frequency = models.CharField(max_length=100, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    source = models.CharField(max_length=30, choices=SOURCE_CHOICES, default="prescription")
    source_reference_id = models.UUIDField(null=True, blank=True)  # FK to prescription/order
    prescriber_id = models.UUIDField(null=True, blank=True)
    recorded_by = models.UUIDField(null=True, blank=True)
    fhir_medication_statement_id = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "cymed_rx_medication_history"
        indexes = [
            models.Index(fields=["patient_id", "is_active"]),
            models.Index(fields=["patient_id", "drug_code"]),
            models.Index(fields=["tenant_id", "start_date"]),
        ]
