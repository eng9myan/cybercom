"""
CyMed Pharmacy — Medication Reconciliation Module
Models: MedicationReconciliation, MedicationHistory (ref. prescriptions),
        MedicationChange, MedicationConflict

Supports: Admission, Transfer, Discharge reconciliation.
Terminology: Drug codes via TerminologyService (RxNorm, SNOMED).
FHIR: MedicationStatement, MedicationAdministration.
"""
from django.db import models
from platform.common.models import BaseModel


class ReconciliationType(models.TextChoices):
    ADMISSION = "admission", "Admission Reconciliation"
    TRANSFER = "transfer", "Transfer Reconciliation"
    DISCHARGE = "discharge", "Discharge Reconciliation"
    PRE_OPERATIVE = "pre_operative", "Pre-Operative"
    POST_OPERATIVE = "post_operative", "Post-Operative"


class ReconciliationStatus(models.TextChoices):
    INITIATED = "initiated", "Initiated"
    IN_PROGRESS = "in_progress", "In Progress"
    PHARMACIST_REVIEW = "pharmacist_review", "Under Pharmacist Review"
    COMPLETED = "completed", "Completed"
    CANCELLED = "cancelled", "Cancelled"


class MedicationReconciliation(BaseModel):
    """
    Formal medication reconciliation record for a patient transition point.
    Ensures complete medication list accuracy at admission, transfer, and discharge.
    FHIR: MedicationStatement collection per patient encounter.
    """
    patient_id = models.UUIDField(db_index=True)
    encounter_id = models.UUIDField(db_index=True)
    admission_id = models.UUIDField(null=True, blank=True)
    reconciliation_type = models.CharField(
        max_length=30, choices=ReconciliationType.choices, default=ReconciliationType.ADMISSION
    )
    status = models.CharField(
        max_length=30, choices=ReconciliationStatus.choices, default=ReconciliationStatus.INITIATED
    )
    initiated_by = models.UUIDField()                                  # Nurse or pharmacist
    pharmacist_id = models.UUIDField(null=True, blank=True)
    prescriber_id = models.UUIDField(null=True, blank=True)

    # Medication lists
    home_medications = models.JSONField(default=list)                  # Patient-reported list
    current_medications = models.JSONField(default=list)               # Active prescriptions/orders
    reconciled_medications = models.JSONField(default=list)            # Final verified list

    # Information sources used
    sources_consulted = models.JSONField(default=list)                 # ["patient", "caregiver", "pharmacy", "emr"]
    medications_count = models.PositiveSmallIntegerField(default=0)
    conflicts_identified = models.PositiveSmallIntegerField(default=0)
    changes_made = models.PositiveSmallIntegerField(default=0)

    completed_at = models.DateTimeField(null=True, blank=True)
    summary_notes = models.TextField(blank=True)

    # FHIR
    fhir_bundle_id = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "cymed_rx_med_reconciliation"
        indexes = [
            models.Index(fields=["patient_id", "reconciliation_type"]),
            models.Index(fields=["encounter_id", "status"]),
            models.Index(fields=["tenant_id", "reconciliation_type", "status"]),
        ]

    def __str__(self):
        return f"Reconciliation [{self.reconciliation_type}] — Patient {self.patient_id}"


class MedicationChange(BaseModel):
    """
    Records each medication change identified during reconciliation.
    Documents why a medication was continued, discontinued, modified, or added.
    """
    CHANGE_TYPES = [
        ("continued", "Continued Unchanged"),
        ("dose_changed", "Dose Changed"),
        ("frequency_changed", "Frequency Changed"),
        ("route_changed", "Route Changed"),
        ("discontinued", "Discontinued"),
        ("added", "New Medication Added"),
        ("held", "Temporarily Held"),
        ("substituted", "Substituted with Alternative"),
    ]

    reconciliation = models.ForeignKey(
        MedicationReconciliation, on_delete=models.CASCADE, related_name="medication_changes"
    )
    drug_code = models.CharField(max_length=100, db_index=True)
    drug_name = models.CharField(max_length=500)
    change_type = models.CharField(max_length=30, choices=CHANGE_TYPES)
    previous_dose = models.CharField(max_length=100, blank=True)
    new_dose = models.CharField(max_length=100, blank=True)
    previous_frequency = models.CharField(max_length=100, blank=True)
    new_frequency = models.CharField(max_length=100, blank=True)
    previous_route = models.CharField(max_length=100, blank=True)
    new_route = models.CharField(max_length=100, blank=True)
    reason = models.TextField()
    changed_by = models.UUIDField()
    prescriber_id = models.UUIDField(null=True, blank=True)
    approved_by = models.UUIDField(null=True, blank=True)
    fhir_medication_statement_id = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "cymed_rx_medication_changes"
        indexes = [models.Index(fields=["reconciliation", "change_type"])]


class MedicationConflict(BaseModel):
    """
    Documents discrepancies and conflicts found during reconciliation.
    Requires pharmacist or prescriber resolution before completion.
    """
    CONFLICT_TYPES = [
        ("omission", "Medication Omission"),
        ("commission", "Unintended Medication Added"),
        ("wrong_dose", "Wrong Dose"),
        ("wrong_frequency", "Wrong Frequency"),
        ("wrong_route", "Wrong Route"),
        ("duplicate", "Duplicate Therapy"),
        ("allergy_conflict", "Allergy Conflict"),
        ("interaction_conflict", "Interaction Conflict"),
        ("formulary_conflict", "Non-Formulary Medication"),
    ]
    STATUS_CHOICES = [
        ("unresolved", "Unresolved"),
        ("under_review", "Under Review"),
        ("resolved", "Resolved"),
        ("escalated", "Escalated to Prescriber"),
    ]

    reconciliation = models.ForeignKey(
        MedicationReconciliation, on_delete=models.CASCADE, related_name="conflicts"
    )
    conflict_type = models.CharField(max_length=30, choices=CONFLICT_TYPES)
    drug_code = models.CharField(max_length=100, blank=True)
    drug_name = models.CharField(max_length=500, blank=True)
    description = models.TextField()
    clinical_significance = models.CharField(
        max_length=20,
        choices=[("minor", "Minor"), ("moderate", "Moderate"), ("major", "Major")],
        default="moderate"
    )
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default="unresolved")
    resolved_by = models.UUIDField(null=True, blank=True)
    resolution_notes = models.TextField(blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "cymed_rx_medication_conflicts"
        indexes = [models.Index(fields=["reconciliation", "status"])]
