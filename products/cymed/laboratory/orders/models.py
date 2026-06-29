"""
CyMed Laboratory — Order Management
Covers: LabTest, LabPanel, LabOrder, LabOrderItem, LabPriority,
        LabOrderStatus, LabOrderDiagnosis, LabOrderAttachment
Terminology: All test codes map to LOINC via TerminologyService (no local LOINC store).
"""

from django.db import models

from platform.common.models import BaseModel


class LabPriority(models.TextChoices):
    STAT = "stat", "STAT"
    URGENT = "urgent", "Urgent"
    ROUTINE = "routine", "Routine"
    TIMED = "timed", "Timed"
    FASTING = "fasting", "Fasting"


class LabTestCategory(models.TextChoices):
    CHEMISTRY = "chemistry", "Chemistry"
    HEMATOLOGY = "hematology", "Hematology"
    IMMUNOLOGY = "immunology", "Immunology"
    SEROLOGY = "serology", "Serology"
    MICROBIOLOGY = "microbiology", "Microbiology"
    PATHOLOGY = "pathology", "Pathology"
    MOLECULAR = "molecular", "Molecular Diagnostics"
    BLOOD_BANK = "blood_bank", "Blood Bank"
    URINALYSIS = "urinalysis", "Urinalysis"
    TOXICOLOGY = "toxicology", "Toxicology"


class LabTest(BaseModel):
    """Master test catalog entry. LOINC codes resolved via TerminologyService — not stored locally."""

    code = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=255)
    name_ar = models.CharField(max_length=255, blank=True)
    loinc_code = models.CharField(max_length=20, blank=True, db_index=True)
    snomed_code = models.CharField(max_length=50, blank=True)
    category = models.CharField(
        max_length=50, choices=LabTestCategory.choices, default=LabTestCategory.CHEMISTRY
    )
    department = models.CharField(max_length=100, blank=True)
    specimen_types_accepted = models.JSONField(default=list)  # ["blood", "serum", "urine"]
    container_types = models.JSONField(default=list)  # ["edta", "sst", "plain"]
    turn_around_hours = models.PositiveIntegerField(default=24)
    stat_tat_hours = models.PositiveIntegerField(default=2)
    unit = models.CharField(max_length=50, blank=True)
    method = models.CharField(max_length=100, blank=True)
    analyzer_code = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    requires_fasting = models.BooleanField(default=False)
    requires_clinical_info = models.BooleanField(default=False)
    patient_preparation = models.TextField(blank=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "cymed_lab_tests"

    def __str__(self):
        return f"{self.code} — {self.name}"


class LabPanel(BaseModel):
    """A named group of tests ordered together (e.g., Metabolic Panel, CBC with Differential)."""

    code = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=255)
    name_ar = models.CharField(max_length=255, blank=True)
    loinc_code = models.CharField(max_length=20, blank=True)
    category = models.CharField(
        max_length=50, choices=LabTestCategory.choices, default=LabTestCategory.CHEMISTRY
    )
    tests = models.ManyToManyField(LabTest, related_name="panels", blank=True)
    is_active = models.BooleanField(default=True)
    is_orderable = models.BooleanField(default=True)
    cpt_code = models.CharField(max_length=20, blank=True)

    class Meta:
        db_table = "cymed_lab_panels"

    def __str__(self):
        return self.name


class LabOrder(BaseModel):
    """A laboratory order from a clinical source (clinic, hospital, external)."""

    ORDER_TYPES = [
        ("hospital", "Hospital Inpatient"),
        ("clinic", "Outpatient Clinic"),
        ("external", "External Referral"),
        ("standing", "Standing Order"),
        ("stat_manual", "STAT Manual"),
    ]
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("submitted", "Submitted"),
        ("in_progress", "In Progress"),
        ("partial", "Partially Resulted"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
        ("on_hold", "On Hold"),
    ]

    order_number = models.CharField(max_length=100, unique=True)
    patient_id = models.UUIDField(db_index=True)
    encounter_id = models.UUIDField(null=True, blank=True, db_index=True)
    admission_id = models.UUIDField(null=True, blank=True)
    order_type = models.CharField(max_length=30, choices=ORDER_TYPES, default="clinic")
    priority = models.CharField(
        max_length=20, choices=LabPriority.choices, default=LabPriority.ROUTINE
    )
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default="submitted")
    ordered_by = models.UUIDField()  # provider_id from CyIdentity
    ordering_location = models.CharField(max_length=255, blank=True)
    clinical_notes = models.TextField(blank=True)
    collected_at = models.DateTimeField(null=True, blank=True)
    requested_at = models.DateTimeField(null=True, blank=True)
    fhir_service_request_id = models.CharField(max_length=255, blank=True)
    hl7_placer_order_number = models.CharField(max_length=100, blank=True)

    class Meta:
        db_table = "cymed_lab_orders"
        indexes = [
            models.Index(fields=["patient_id", "status"]),
            models.Index(fields=["tenant_id", "order_type", "priority"]),
        ]

    def __str__(self):
        return self.order_number


class LabOrderItem(BaseModel):
    """Individual test or panel line within a lab order."""

    STATUS_CHOICES = [
        ("ordered", "Ordered"),
        ("collected", "Specimen Collected"),
        ("received", "Specimen Received"),
        ("in_progress", "In Progress"),
        ("resulted", "Resulted"),
        ("verified", "Verified"),
        ("approved", "Approved"),
        ("cancelled", "Cancelled"),
        ("on_hold", "On Hold"),
        ("referred", "Referred to Reference Lab"),
    ]

    order = models.ForeignKey(LabOrder, on_delete=models.CASCADE, related_name="items")
    test = models.ForeignKey(
        LabTest, on_delete=models.PROTECT, null=True, blank=True, related_name="order_items"
    )
    panel = models.ForeignKey(
        LabPanel, on_delete=models.PROTECT, null=True, blank=True, related_name="order_items"
    )
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default="ordered")
    priority = models.CharField(
        max_length=20, choices=LabPriority.choices, default=LabPriority.ROUTINE
    )
    specimen_type = models.CharField(max_length=100, blank=True)
    requested_at = models.DateTimeField(auto_now_add=True)
    resulted_at = models.DateTimeField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    cancelled_reason = models.TextField(blank=True)
    worklist_assigned = models.BooleanField(default=False)

    class Meta:
        db_table = "cymed_lab_order_items"
        indexes = [models.Index(fields=["order", "status"])]


class LabOrderDiagnosis(BaseModel):
    """ICD-11 diagnoses associated with the order (resolved via TerminologyService)."""

    order = models.ForeignKey(LabOrder, on_delete=models.CASCADE, related_name="diagnoses")
    icd11_code = models.CharField(max_length=20)
    description = models.CharField(max_length=500, blank=True)
    is_primary = models.BooleanField(default=False)

    class Meta:
        db_table = "cymed_lab_order_diagnoses"


class LabOrderAttachment(BaseModel):
    """Documents/images attached to a lab order (referral letter, requisition scan)."""

    order = models.ForeignKey(LabOrder, on_delete=models.CASCADE, related_name="attachments")
    file_name = models.CharField(max_length=255)
    file_type = models.CharField(max_length=50)
    file_url = models.URLField(max_length=1000)
    uploaded_by = models.UUIDField()
    description = models.CharField(max_length=500, blank=True)

    class Meta:
        db_table = "cymed_lab_order_attachments"


class LabOrderStatusHistory(BaseModel):
    """Immutable audit trail of status transitions for a lab order."""

    order = models.ForeignKey(LabOrder, on_delete=models.CASCADE, related_name="status_history")
    from_status = models.CharField(max_length=30)
    to_status = models.CharField(max_length=30)
    changed_by = models.UUIDField(null=True, blank=True)
    reason = models.CharField(max_length=255, blank=True)
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "cymed_lab_order_status_history"
        ordering = ["-changed_at"]
