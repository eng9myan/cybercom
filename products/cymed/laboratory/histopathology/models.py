"""
CyMed Laboratory â€” Histopathology
Tissue block, slide, and review workflow downstream of PathologyCase.
"""
from django.db import models
from platform.common.models import BaseModel


class HistologyCaseStatus(models.TextChoices):
    RECEIVED = "received", "Case Received"
    EMBEDDING = "embedding", "Embedding"
    SECTIONING = "sectioning", "Sectioning"
    STAINING = "staining", "Staining"
    READY_FOR_REVIEW = "ready_for_review", "Ready for Pathologist Review"
    UNDER_REVIEW = "under_review", "Under Review"
    ADDITIONAL_STAINS = "additional_stains", "Additional Stains Requested"
    SIGNED_OUT = "signed_out", "Signed Out"


class HistologyCase(BaseModel):
    """Histology workflow case â€” linked to a PathologyCase."""
    pathology_case = models.OneToOneField(
        "lab_pathology.PathologyCase", on_delete=models.CASCADE, related_name="histology_case"
    )
    case_number = models.CharField(max_length=100, unique=True, db_index=True)
    status = models.CharField(
        max_length=30, choices=HistologyCaseStatus.choices, default=HistologyCaseStatus.RECEIVED
    )
    assigned_histotechnician = models.UUIDField(null=True, blank=True)
    opened_at = models.DateTimeField(auto_now_add=True)
    signed_out_at = models.DateTimeField(null=True, blank=True)
    turnaround_hours = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        db_table = "cymed_lab_histology_cases"

    def __str__(self):
        return self.case_number


class TissueBlock(BaseModel):
    """Paraffin-embedded tissue block produced from a pathology specimen cassette."""
    EMBEDDING_STATUS = [
        ("pending", "Pending Embedding"),
        ("embedded", "Embedded"),
        ("sectioned", "Sectioned"),
        ("archived", "Archived"),
        ("depleted", "Depleted"),
    ]

    case = models.ForeignKey(HistologyCase, on_delete=models.CASCADE, related_name="blocks")
    block_number = models.CharField(max_length=20)
    cassette_number = models.CharField(max_length=20)
    pathology_specimen = models.ForeignKey(
        "lab_pathology.PathologySpecimen", on_delete=models.PROTECT, related_name="tissue_blocks", null=True, blank=True
    )
    tissue_type = models.CharField(max_length=100, blank=True)
    embedding_status = models.CharField(max_length=20, choices=EMBEDDING_STATUS, default="pending")
    embedded_by = models.UUIDField(null=True, blank=True)
    embedded_at = models.DateTimeField(null=True, blank=True)
    storage_location = models.CharField(max_length=100, blank=True)

    class Meta:
        db_table = "cymed_lab_tissue_blocks"
        unique_together = [("case", "block_number")]


class Slide(BaseModel):
    """Glass slide cut from a tissue block, stained, and reviewed by pathologist."""
    STAIN_TYPES = [
        ("he", "H&E â€” Hematoxylin & Eosin"),
        ("pas", "PAS â€” Periodic Acid-Schiff"),
        ("giemsa", "Giemsa"),
        ("gram", "Gram Stain"),
        ("zn", "Ziehl-Neelsen (ZN)"),
        ("masson", "Masson Trichrome"),
        ("reticulin", "Reticulin"),
        ("oil_red_o", "Oil Red O"),
        ("congo_red", "Congo Red"),
        ("ihc", "IHC â€” Immunohistochemistry"),
        ("fish", "FISH"),
        ("pcr", "Molecular PCR"),
        ("other", "Other"),
    ]
    QUALITY_GRADES = [
        ("optimal", "Optimal"),
        ("acceptable", "Acceptable"),
        ("suboptimal", "Suboptimal"),
        ("unacceptable", "Unacceptable â€” Recut"),
    ]

    block = models.ForeignKey(TissueBlock, on_delete=models.CASCADE, related_name="slides")
    slide_number = models.CharField(max_length=20)
    stain_type = models.CharField(max_length=20, choices=STAIN_TYPES, default="he")
    stain_status = models.CharField(max_length=20, default="pending")
    quality_grade = models.CharField(max_length=20, choices=QUALITY_GRADES, blank=True)
    cut_thickness_microns = models.PositiveSmallIntegerField(null=True, blank=True)
    stained_by = models.UUIDField(null=True, blank=True)
    stained_at = models.DateTimeField(null=True, blank=True)
    barcode = models.CharField(max_length=100, unique=True, blank=True)
    digital_scan_url = models.URLField(max_length=2000, blank=True)
    is_request = models.BooleanField(default=False)  # True if pathologist requested additional stain

    class Meta:
        db_table = "cymed_lab_slides"
        unique_together = [("block", "slide_number")]


class SlideReview(BaseModel):
    """Pathologist review findings for a slide â€” may yield additional stain requests."""
    REVIEW_STATUS = [
        ("pending", "Pending"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("deferred", "Deferred â€” Awaiting Additional Stain"),
    ]

    slide = models.ForeignKey(Slide, on_delete=models.CASCADE, related_name="reviews")
    reviewed_by = models.UUIDField()
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_status = models.CharField(max_length=20, choices=REVIEW_STATUS, default="pending")
    findings = models.TextField(blank=True)
    additional_stains_requested = models.JSONField(default=list)
    ai_assistance_used = models.BooleanField(default=False)
    ai_suggestions = models.JSONField(default=dict)

    class Meta:
        db_table = "cymed_lab_slide_reviews"


class HistologyDiagnosis(BaseModel):
    """Final histological diagnosis for a case."""
    DIAGNOSIS_CATEGORIES = [
        ("benign", "Benign"),
        ("malignant", "Malignant"),
        ("borderline", "Borderline"),
        ("inflammatory", "Inflammatory"),
        ("reactive", "Reactive"),
        ("normal", "Normal Tissue"),
        ("inconclusive", "Inconclusive"),
    ]

    case = models.ForeignKey(HistologyCase, on_delete=models.CASCADE, related_name="diagnoses")
    snomed_code = models.CharField(max_length=50, blank=True)    # via TerminologyService
    icd11_code = models.CharField(max_length=20, blank=True)     # via TerminologyService
    diagnosis_text = models.TextField()
    diagnosis_category = models.CharField(max_length=20, choices=DIAGNOSIS_CATEGORIES, blank=True)
    comment = models.TextField(blank=True)
    signed_by = models.UUIDField(null=True, blank=True)
    signed_at = models.DateTimeField(null=True, blank=True)
    digital_signature = models.CharField(max_length=512, blank=True)

    class Meta:
        db_table = "cymed_lab_histology_diagnoses"
