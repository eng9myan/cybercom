"""
CyMed Laboratory â€” Pathology
Surgical pathology case management: gross, microscopic, diagnosis workflow.
Diagnosis codes from SNOMED-CT + ICD-11 via TerminologyService.
"""
from django.db import models
from platform.common.models import BaseModel


class PathologyCaseStatus(models.TextChoices):
    RECEIVED = "received", "Received"
    GROSSING = "grossing", "Grossing"
    PROCESSING = "processing", "Tissue Processing"
    SECTIONING = "sectioning", "Sectioning and Staining"
    MICROSCOPY = "microscopy", "Microscopic Examination"
    DRAFT_REPORT = "draft_report", "Draft Report"
    PATHOLOGIST_REVIEW = "pathologist_review", "Pathologist Review"
    SIGNED_OUT = "signed_out", "Signed Out"
    AMENDED = "amended", "Amended"


class PathologyCase(BaseModel):
    """Surgical pathology case â€” tracks tissue from receipt through final diagnosis."""
    order_item = models.ForeignKey(
        "lab_orders.LabOrderItem", on_delete=models.CASCADE, related_name="pathology_cases"
    )
    case_number = models.CharField(max_length=100, unique=True, db_index=True)
    patient_id = models.UUIDField(db_index=True)
    clinical_history = models.TextField()
    preoperative_diagnosis = models.CharField(max_length=500, blank=True)
    procedure_type = models.CharField(max_length=200, blank=True)
    operating_surgeon = models.UUIDField(null=True, blank=True)
    specimen_received_at = models.DateTimeField(null=True, blank=True)
    received_by = models.UUIDField(null=True, blank=True)
    status = models.CharField(
        max_length=30, choices=PathologyCaseStatus.choices, default=PathologyCaseStatus.RECEIVED
    )
    assigned_pathologist = models.UUIDField(null=True, blank=True)
    priority = models.CharField(max_length=20, default="routine")
    fhir_diagnostic_report_id = models.CharField(max_length=255, blank=True)
    is_intraoperative = models.BooleanField(default=False)

    class Meta:
        db_table = "cymed_lab_pathology_cases"
        indexes = [models.Index(fields=["tenant_id", "status", "assigned_pathologist"])]

    def __str__(self):
        return self.case_number


class PathologySpecimen(BaseModel):
    """Individual tissue specimen within a pathology case."""
    case = models.ForeignKey(PathologyCase, on_delete=models.CASCADE, related_name="specimens")
    specimen = models.ForeignKey(
        "lab_specimens.Specimen", on_delete=models.PROTECT, null=True, blank=True, related_name="pathology_specimens"
    )
    part_label = models.CharField(max_length=10)     # A, B, C, etc.
    description = models.CharField(max_length=500)
    specimen_site = models.CharField(max_length=255, blank=True)
    snomed_site_code = models.CharField(max_length=50, blank=True)   # via TerminologyService
    fixative = models.CharField(max_length=100, default="formalin")
    cassettes_submitted = models.PositiveSmallIntegerField(default=0)
    weight_grams = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    dimensions = models.CharField(max_length=100, blank=True)

    class Meta:
        db_table = "cymed_lab_pathology_specimens"
        unique_together = [("case", "part_label")]


class GrossExamination(BaseModel):
    """Macroscopic/gross description of a pathology specimen."""
    case = models.ForeignKey(PathologyCase, on_delete=models.CASCADE, related_name="gross_examinations")
    pathology_specimen = models.OneToOneField(
        PathologySpecimen, on_delete=models.CASCADE, related_name="gross_examination"
    )
    gross_description = models.TextField()
    representative_sections = models.TextField(blank=True)
    examined_by = models.UUIDField()
    examined_at = models.DateTimeField()
    inked = models.BooleanField(default=False)
    ink_colors = models.CharField(max_length=100, blank=True)
    tumor_size_cm = models.CharField(max_length=50, blank=True)
    margin_involvement = models.CharField(max_length=100, blank=True)

    class Meta:
        db_table = "cymed_lab_gross_examinations"


class MicroscopicExamination(BaseModel):
    """Histological microscopic examination findings by pathologist."""
    case = models.ForeignKey(PathologyCase, on_delete=models.CASCADE, related_name="microscopic_examinations")
    pathology_specimen = models.ForeignKey(
        PathologySpecimen, on_delete=models.CASCADE, related_name="microscopic_examinations"
    )
    microscopic_description = models.TextField()
    stains_used = models.JSONField(default=list)          # ["H&E", "PAS", "ZN", "Reticulin"]
    special_stains = models.JSONField(default=list)
    ihc_markers = models.JSONField(default=dict)          # {"ER": "Positive 90%", "PR": "Negative"}
    examined_by = models.UUIDField()
    examined_at = models.DateTimeField()

    class Meta:
        db_table = "cymed_lab_microscopic_examinations"


class PathologyDiagnosis(BaseModel):
    """Final pathological diagnosis for a case part."""
    DIAGNOSIS_CATEGORIES = [
        ("benign", "Benign"),
        ("malignant", "Malignant"),
        ("borderline", "Borderline/Uncertain"),
        ("inflammatory", "Inflammatory"),
        ("reactive", "Reactive"),
        ("normal", "Within Normal Limits"),
        ("inconclusive", "Inconclusive"),
    ]

    case = models.ForeignKey(PathologyCase, on_delete=models.CASCADE, related_name="diagnoses")
    pathology_specimen = models.ForeignKey(
        PathologySpecimen, on_delete=models.CASCADE, related_name="diagnoses", null=True, blank=True
    )
    snomed_code = models.CharField(max_length=50, blank=True)       # SNOMED-CT via TerminologyService
    icd11_code = models.CharField(max_length=20, blank=True)         # ICD-11 via TerminologyService
    diagnosis_text = models.TextField()
    diagnosis_category = models.CharField(max_length=20, choices=DIAGNOSIS_CATEGORIES, blank=True)
    tnm_staging = models.CharField(max_length=50, blank=True)
    grade = models.CharField(max_length=50, blank=True)
    is_primary = models.BooleanField(default=True)
    signed_by = models.UUIDField(null=True, blank=True)
    signed_at = models.DateTimeField(null=True, blank=True)
    digital_signature = models.CharField(max_length=512, blank=True)

    class Meta:
        db_table = "cymed_lab_pathology_diagnoses"
