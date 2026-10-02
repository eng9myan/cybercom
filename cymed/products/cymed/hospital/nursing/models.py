from django.db import models

from platform.common.fields import EncryptedText
from platform.common.models import BaseModel
from products.cymed.hospital.adt.models import Admission


class NursingShift(BaseModel):
    name = models.CharField(max_length=100)  # Day shift, Night shift
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        db_table = "cymed_hospital_nursing_shifts"


class NursingAssignment(BaseModel):
    nurse_id = models.UUIDField()
    ward_id = models.UUIDField()
    shift = models.ForeignKey(NursingShift, on_delete=models.CASCADE)
    assigned_date = models.DateField()

    class Meta:
        db_table = "cymed_hospital_nursing_assignments"


class NursingAssessment(BaseModel):
    admission = models.ForeignKey(Admission, on_delete=models.CASCADE)
    assessed_by = models.UUIDField()
    assessed_at = models.DateTimeField(auto_now_add=True)
    nursing_summary = EncryptedText(classification="phi")

    class Meta:
        db_table = "cymed_hospital_nursing_assessments"


class NursingCarePlan(BaseModel):
    admission = models.ForeignKey(Admission, on_delete=models.CASCADE)
    goals = EncryptedText(classification="phi")
    activities = EncryptedText(classification="phi")

    class Meta:
        db_table = "cymed_hospital_nursing_careplans"


class NursingTask(BaseModel):
    admission = models.ForeignKey(Admission, on_delete=models.CASCADE)
    task_name = models.CharField(max_length=255)
    scheduled_at = models.DateTimeField()
    completed_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=50,
        choices=[("pending", "Pending"), ("completed", "Completed"), ("skipped", "Skipped")],
        default="pending",
    )

    class Meta:
        db_table = "cymed_hospital_nursing_tasks"


class NursingHandover(BaseModel):
    admission = models.ForeignKey(Admission, on_delete=models.CASCADE)
    outgoing_nurse_id = models.UUIDField()
    incoming_nurse_id = models.UUIDField()
    handover_time = models.DateTimeField(auto_now_add=True)
    situation_background = EncryptedText(classification="phi")  # SBAR format
    assessment_recommendation = EncryptedText(classification="phi")

    class Meta:
        db_table = "cymed_hospital_nursing_handovers"


class MedicationAdministration(BaseModel):
    """One dose on the electronic Medication Administration Record (eMAR).

    Scheduled rows are generated from an active inpatient MedicationOrder;
    PRN / STAT doses are recorded ad hoc. Giving a dose goes through the
    "five rights" check in services.administer(): right patient (wristband
    scan), right drug (package scan), right dose, right route, right time —
    plus an independent witness for controlled drugs.
    """

    STATUS = [
        ("scheduled", "Scheduled"),
        ("given", "Given"),
        ("held", "Held"),
        ("refused", "Refused by patient"),
        ("missed", "Missed"),
    ]

    medication_order = models.ForeignKey(
        "cymed_pharmacy_prescriptions.MedicationOrder",
        on_delete=models.PROTECT,
        related_name="administrations",
    )
    patient_id = models.UUIDField(db_index=True)
    admission_id = models.UUIDField(db_index=True)
    status = models.CharField(max_length=20, choices=STATUS, default="scheduled", db_index=True)
    scheduled_at = models.DateTimeField(null=True, blank=True, db_index=True)  # null = PRN/ad hoc
    administered_at = models.DateTimeField(null=True, blank=True)
    administered_by = models.CharField(max_length=255, blank=True)
    witnessed_by = models.CharField(max_length=255, blank=True)
    dose_given = models.CharField(max_length=100, blank=True)
    dose_unit = models.CharField(max_length=50, blank=True)
    route = models.CharField(max_length=100, blank=True)
    site = models.CharField(max_length=100, blank=True)
    patient_barcode_verified = models.BooleanField(default=False)
    medication_barcode_verified = models.BooleanField(default=False)
    # Why a dose was held / refused / given PRN / given outside its window /
    # given at a dose that differs from the order.
    reason = models.TextField(blank=True)
    notes = EncryptedText(classification="phi", blank=True, default=b"")

    class Meta:
        db_table = "cymed_nursing_medication_administrations"
        ordering = ["scheduled_at", "administered_at"]
        indexes = [models.Index(fields=["tenant_id", "admission_id", "status"])]
        constraints = [
            models.UniqueConstraint(
                fields=["medication_order", "scheduled_at"],
                condition=models.Q(scheduled_at__isnull=False),
                name="uniq_mar_dose_per_order_slot",
            )
        ]

    def __str__(self) -> str:
        return f"MAR {self.medication_order_id} @ {self.scheduled_at or 'PRN'} [{self.status}]"
