"""
CyMed Pharmacy — Formulary Management
Models: Formulary, FormularyDrug, FormularyRestriction,
        TherapeuticClass, PreferredMedication

Supports: Hospital, Retail, Government, Pharmacy Chain formularies.
Terminology: Drug codes via TerminologyService (RxNorm, SNOMED).
             Therapeutic classes via SNOMED via TerminologyService.
"""

from django.db import models

from platform.common.models import BaseModel


class FormularyType(models.TextChoices):
    HOSPITAL = "hospital", "Hospital Formulary"
    RETAIL = "retail", "Retail Formulary"
    GOVERNMENT = "government", "Government Formulary"
    INSURANCE = "insurance", "Insurance/Payer Formulary"
    NATIONAL = "national", "National Formulary"
    CHAIN = "chain", "Pharmacy Chain Formulary"


class TherapeuticClass(BaseModel):
    """
    Drug therapeutic classification hierarchy.
    Maps to ATC classification via TerminologyService.
    """

    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)
    name_ar = models.CharField(max_length=255, blank=True)
    atc_code = models.CharField(max_length=20, blank=True)  # ATC via TerminologyService
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.SET_NULL, related_name="children"
    )
    level = models.PositiveSmallIntegerField(default=1)  # 1=class, 2=subclass, 3=drug
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "cymed_formulary_therapeutic_classes"
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} — {self.name}"


class Formulary(BaseModel):
    """
    A formulary defines the approved medication list for a specific context.
    Each tenant may have multiple formularies (hospital, retail, insurance).
    """

    name = models.CharField(max_length=255)
    name_ar = models.CharField(max_length=255, blank=True)
    formulary_type = models.CharField(
        max_length=30, choices=FormularyType.choices, default=FormularyType.HOSPITAL
    )
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    effective_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    managed_by = models.UUIDField(null=True, blank=True)  # Pharmacy Director
    version = models.CharField(max_length=20, default="1.0")
    description = models.TextField(blank=True)

    class Meta:
        db_table = "cymed_formularies"
        indexes = [
            models.Index(fields=["tenant_id", "formulary_type", "is_active"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_formulary_type_display()})"


class FormularyDrug(BaseModel):
    """
    A drug entry in a formulary.
    Drug codes resolved via TerminologyService (RxNorm).
    """

    STATUS_CHOICES = [
        ("preferred", "Preferred"),
        ("non_preferred", "Non-Preferred"),
        ("restricted", "Restricted"),
        ("non_formulary", "Non-Formulary"),
        ("discontinued", "Discontinued"),
    ]
    TIER_CHOICES = [
        (1, "Tier 1 — Generic"),
        (2, "Tier 2 — Preferred Brand"),
        (3, "Tier 3 — Non-Preferred Brand"),
        (4, "Tier 4 — Specialty"),
        (5, "Tier 5 — Biologic"),
    ]

    formulary = models.ForeignKey(Formulary, on_delete=models.CASCADE, related_name="drugs")
    therapeutic_class = models.ForeignKey(
        TherapeuticClass,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="formulary_drugs",
    )

    # Drug identity via TerminologyService
    drug_code = models.CharField(max_length=100, db_index=True)  # RxNorm
    drug_name = models.CharField(max_length=500)
    drug_name_ar = models.CharField(max_length=500, blank=True)
    generic_code = models.CharField(max_length=100, blank=True)
    generic_name = models.CharField(max_length=500, blank=True)
    atc_code = models.CharField(max_length=20, blank=True)

    # Formulary status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="preferred")
    tier = models.PositiveSmallIntegerField(choices=TIER_CHOICES, default=1)
    is_generic_allowed = models.BooleanField(default=True)
    requires_prior_auth = models.BooleanField(default=False)
    requires_step_therapy = models.BooleanField(default=False)

    # Restrictions
    age_restriction_min = models.PositiveSmallIntegerField(null=True, blank=True)
    age_restriction_max = models.PositiveSmallIntegerField(null=True, blank=True)
    gender_restriction = models.CharField(
        max_length=10,
        choices=[("any", "Any"), ("male", "Male Only"), ("female", "Female Only")],
        default="any",
    )
    indication_restrictions = models.JSONField(default=list)  # ICD-11 codes
    quantity_limits = models.JSONField(default=dict)  # {"per_fill": 30, "per_year": 360}

    # Availability
    available_strengths = models.JSONField(default=list)
    available_forms = models.JSONField(default=list)  # tablet, capsule, injection
    dispensing_locations = models.JSONField(default=list)  # ward, outpatient, retail

    effective_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    added_by = models.UUIDField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "cymed_formulary_drugs"
        unique_together = [("formulary", "drug_code")]
        indexes = [
            models.Index(fields=["formulary", "status", "tier"]),
            models.Index(fields=["drug_code", "status"]),
        ]


class FormularyRestriction(BaseModel):
    """
    Additional restriction rules applied to specific formulary drugs.
    Linked to specific criteria (diagnosis, prescriber specialty, etc.)
    """

    RESTRICTION_TYPES = [
        ("diagnosis_required", "Specific Diagnosis Required"),
        ("specialist_only", "Specialist Prescriber Only"),
        ("age_limit", "Age Limit"),
        ("quantity_limit", "Quantity Limit"),
        ("prior_auth", "Prior Authorization"),
        ("step_therapy", "Step Therapy Required"),
        ("lab_required", "Lab Result Required"),
        ("gender_specific", "Gender Specific"),
    ]

    formulary_drug = models.ForeignKey(
        FormularyDrug, on_delete=models.CASCADE, related_name="restrictions"
    )
    restriction_type = models.CharField(max_length=30, choices=RESTRICTION_TYPES)
    description = models.TextField()
    criteria = models.JSONField(default=dict)  # Flexible criteria store
    is_hard_stop = models.BooleanField(default=False)  # Block or warn
    effective_date = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "cymed_formulary_restrictions"


class PreferredMedication(BaseModel):
    """
    Therapeutic interchange — preferred alternatives to non-formulary drugs.
    Used to suggest formulary-compliant substitutes.
    """

    INTERCHANGE_REASON = [
        ("cost", "Cost Reduction"),
        ("formulary_compliance", "Formulary Compliance"),
        ("safety", "Safety Preference"),
        ("efficacy", "Equivalent Efficacy"),
        ("availability", "Drug Availability"),
    ]

    formulary = models.ForeignKey(
        Formulary, on_delete=models.CASCADE, related_name="preferred_medications"
    )
    non_formulary_drug_code = models.CharField(max_length=100, db_index=True)
    non_formulary_drug_name = models.CharField(max_length=500)
    preferred_drug_code = models.CharField(max_length=100, db_index=True)
    preferred_drug_name = models.CharField(max_length=500)
    interchange_reason = models.CharField(
        max_length=30, choices=INTERCHANGE_REASON, default="formulary_compliance"
    )
    dose_conversion_notes = models.TextField(blank=True)
    clinical_notes = models.TextField(blank=True)
    requires_pharmacist_counseling = models.BooleanField(default=True)
    approved_by = models.UUIDField(null=True, blank=True)

    class Meta:
        db_table = "cymed_preferred_medications"
        indexes = [models.Index(fields=["formulary", "non_formulary_drug_code"])]
