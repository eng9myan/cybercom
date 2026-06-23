from django.db import models
from platform.common.models import BaseModel


class PortalPrescriptionView(BaseModel):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('dispensed', 'Dispensed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
        ('on_hold', 'On Hold'),
    ]

    account_id = models.UUIDField(db_index=True)
    patient_id = models.UUIDField(db_index=True)
    cymed_prescription_id = models.UUIDField(db_index=True)
    prescription_number = models.CharField(max_length=100, db_index=True)
    pharmacy_name = models.CharField(max_length=255, blank=True)
    pharmacy_id = models.UUIDField(null=True, blank=True)
    prescriber_name = models.CharField(max_length=255, blank=True)
    prescription_type = models.CharField(max_length=30, blank=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
    )
    is_controlled = models.BooleanField(default=False)
    items_summary = models.JSONField(default=list)
    prescribed_at = models.DateTimeField(null=True, blank=True)
    valid_until = models.DateField(null=True, blank=True)
    refills_authorized = models.PositiveSmallIntegerField(default=0)
    refills_dispensed = models.PositiveSmallIntegerField(default=0)
    can_request_refill = models.BooleanField(default=False)
    is_viewed = models.BooleanField(default=False)
    viewed_at = models.DateTimeField(null=True, blank=True)
    fhir_medication_request_id = models.CharField(
        max_length=255, blank=True, db_index=True
    )

    class Meta:
        db_table = 'cymed_portal_prescriptions'
        indexes = [
            models.Index(
                fields=['account_id', 'status'],
                name='prescriptions_acct_status_idx',
            ),
            models.Index(
                fields=['patient_id', 'prescribed_at'],
                name='prescriptions_patient_date_idx',
            ),
        ]

    def __str__(self):
        return f"Prescription {self.prescription_number} ({self.get_status_display()})"


class RefillRequest(BaseModel):
    PICKUP_METHOD_CHOICES = [
        ('counter', 'Counter Pickup'),
        ('delivery', 'Delivery'),
        ('mail', 'Mail'),
    ]

    STATUS_CHOICES = [
        ('submitted', 'Submitted'),
        ('received_by_pharmacy', 'Received by Pharmacy'),
        ('processing', 'Processing'),
        ('ready', 'Ready'),
        ('dispensed', 'Dispensed'),
        ('cancelled', 'Cancelled'),
    ]

    account_id = models.UUIDField(db_index=True)
    patient_id = models.UUIDField(db_index=True)
    portal_prescription = models.ForeignKey(
        PortalPrescriptionView,
        on_delete=models.CASCADE,
        related_name='refill_requests',
    )
    preferred_pharmacy_id = models.UUIDField(null=True, blank=True)
    preferred_pharmacy_name = models.CharField(max_length=255, blank=True)
    pickup_method = models.CharField(
        max_length=20,
        choices=PICKUP_METHOD_CHOICES,
        default='counter',
    )
    delivery_address = models.CharField(max_length=500, blank=True)
    notes = models.TextField(blank=True)
    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default='submitted',
    )
    submitted_at = models.DateTimeField(auto_now_add=True)
    pharmacy_response = models.TextField(blank=True)
    estimated_ready_at = models.DateTimeField(null=True, blank=True)
    cymed_dispense_id = models.UUIDField(null=True, blank=True)

    class Meta:
        db_table = 'cymed_portal_refill_requests'
        indexes = [
            models.Index(
                fields=['account_id', 'status'],
                name='refill_requests_acct_status_idx',
            ),
        ]

    def __str__(self):
        return (
            f"Refill request for {self.portal_prescription} "
            f"({self.get_status_display()})"
        )


class MedicationInstruction(BaseModel):
    account_id = models.UUIDField(db_index=True)
    patient_id = models.UUIDField(db_index=True)
    drug_code = models.CharField(max_length=100, db_index=True)
    drug_name = models.CharField(max_length=500)
    instruction_text = models.TextField()
    instruction_text_ar = models.TextField(blank=True)
    dose = models.CharField(max_length=100, blank=True)
    frequency = models.CharField(max_length=100, blank=True)
    route = models.CharField(max_length=100, blank=True)
    special_warnings = models.JSONField(default=list)
    side_effects = models.JSONField(default=list)
    ai_explanation = models.TextField(blank=True)

    class Meta:
        db_table = 'cymed_portal_medication_instructions'
        unique_together = [('tenant_id', 'patient_id', 'drug_code')]

    def __str__(self):
        return f"{self.drug_name} ({self.drug_code}) instructions"


class MedicationAdherenceLog(BaseModel):
    STATUS_CHOICES = [
        ('taken', 'Taken'),
        ('missed', 'Missed'),
        ('skipped', 'Skipped'),
        ('rescheduled', 'Rescheduled'),
    ]

    account_id = models.UUIDField(db_index=True)
    patient_id = models.UUIDField(db_index=True)
    portal_prescription = models.ForeignKey(
        PortalPrescriptionView,
        on_delete=models.CASCADE,
        related_name='adherence_logs',
    )
    drug_code = models.CharField(max_length=100)
    drug_name = models.CharField(max_length=500)
    scheduled_time = models.DateTimeField()
    taken_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='taken',
    )
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'cymed_portal_adherence_logs'
        indexes = [
            models.Index(
                fields=['account_id', 'status', 'scheduled_time'],
                name='adherence_logs_acct_status_time_idx',
            ),
        ]

    def __str__(self):
        return (
            f"{self.drug_name} adherence — {self.get_status_display()} "
            f"at {self.scheduled_time}"
        )
