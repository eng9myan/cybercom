"""
CyMed Laboratory â€” Microbiology
Culture tracking, organism ID, antibiotic sensitivity, resistance profiling.
Organism codes resolved via SNOMED-CT through TerminologyService.
"""

from django.db import models

from platform.common.models import BaseModel


class CultureStatus(models.TextChoices):
    PENDING = "pending", "Pending Inoculation"
    INOCULATED = "inoculated", "Inoculated"
    INCUBATING = "incubating", "Incubating"
    NO_GROWTH = "no_growth", "No Growth at 24h"
    PRELIMINARY = "preliminary", "Preliminary Result"
    FINAL = "final", "Final Result"
    AMENDED = "amended", "Amended"


class SensitivityResult(models.TextChoices):
    SUSCEPTIBLE = "S", "Susceptible"
    INTERMEDIATE = "I", "Intermediate"
    RESISTANT = "R", "Resistant"
    NOT_APPLICABLE = "NA", "Not Applicable"
    NOT_TESTED = "NT", "Not Tested"


class Culture(BaseModel):
    """Tracks a single microbiology culture from inoculation through result."""

    order_item = models.ForeignKey(
        "lab_orders.LabOrderItem", on_delete=models.CASCADE, related_name="cultures"
    )
    specimen = models.ForeignKey(
        "lab_specimens.Specimen", on_delete=models.PROTECT, related_name="cultures"
    )
    culture_number = models.CharField(max_length=100, unique=True)
    culture_type = models.CharField(max_length=100)  # aerobic, anaerobic, fungal, TB, viral
    medium = models.CharField(max_length=100, blank=True)
    incubation_temperature_celsius = models.DecimalField(
        max_digits=5, decimal_places=1, null=True, blank=True
    )
    incubation_hours = models.PositiveIntegerField(default=24)
    status = models.CharField(
        max_length=20, choices=CultureStatus.choices, default=CultureStatus.PENDING
    )
    inoculated_at = models.DateTimeField(null=True, blank=True)
    inoculated_by = models.UUIDField(null=True, blank=True)
    read_at_24h = models.DateTimeField(null=True, blank=True)
    read_at_48h = models.DateTimeField(null=True, blank=True)
    read_at_72h = models.DateTimeField(null=True, blank=True)
    final_read_at = models.DateTimeField(null=True, blank=True)
    comments = models.TextField(blank=True)

    class Meta:
        db_table = "cymed_lab_cultures"
        indexes = [models.Index(fields=["tenant_id", "status"])]

    def __str__(self):
        return self.culture_number


class Organism(BaseModel):
    """Organism identified from a culture. SNOMED-CT code from TerminologyService."""

    GRAM_STAIN = [
        ("gram_positive", "Gram Positive"),
        ("gram_negative", "Gram Negative"),
        ("gram_variable", "Gram Variable"),
        ("not_applicable", "Not Applicable"),
        ("unknown", "Unknown"),
    ]
    MORPHOLOGY = [
        ("cocci", "Cocci"),
        ("bacilli", "Bacilli"),
        ("coccobacilli", "Coccobacilli"),
        ("spirochete", "Spirochete"),
        ("yeast", "Yeast"),
        ("mold", "Mold"),
        ("other", "Other"),
    ]
    GROWTH_LEVEL = [
        ("none", "No Growth"),
        ("rare", "Rare (< 10 CFU)"),
        ("few", "Few (10â€“100 CFU)"),
        ("moderate", "Moderate (100â€“1000 CFU)"),
        ("many", "Many (> 1000 CFU)"),
        ("heavy", "Heavy (Confluent)"),
    ]

    culture = models.ForeignKey(Culture, on_delete=models.CASCADE, related_name="organisms")
    snomed_code = models.CharField(max_length=50, blank=True)  # SNOMED-CT via TerminologyService
    organism_name = models.CharField(max_length=255)
    gram_stain = models.CharField(max_length=20, choices=GRAM_STAIN, blank=True)
    morphology = models.CharField(max_length=20, choices=MORPHOLOGY, blank=True)
    growth_level = models.CharField(max_length=20, choices=GROWTH_LEVEL, blank=True)
    identification_method = models.CharField(max_length=100, blank=True)  # MALDI-TOF, API, VITEK
    identification_confidence = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    is_contaminant = models.BooleanField(default=False)
    identified_at = models.DateTimeField(null=True, blank=True)
    identified_by = models.UUIDField(null=True, blank=True)

    class Meta:
        db_table = "cymed_lab_organisms"


class Sensitivity(BaseModel):
    """Antibiotic sensitivity test result for a single drug-organism pair."""

    organism = models.ForeignKey(Organism, on_delete=models.CASCADE, related_name="sensitivities")
    antibiotic_code = models.CharField(max_length=50)
    antibiotic_name = models.CharField(max_length=255)
    method = models.CharField(max_length=50, blank=True)  # disk_diffusion, MIC, E-test
    result = models.CharField(
        max_length=5, choices=SensitivityResult.choices, default=SensitivityResult.NOT_TESTED
    )
    mic_value = models.CharField(max_length=20, blank=True)  # e.g., "<=0.5", "16", ">128"
    disk_zone_mm = models.PositiveSmallIntegerField(null=True, blank=True)
    breakpoint_standard = models.CharField(max_length=50, blank=True)  # CLSI, EUCAST
    tested_at = models.DateTimeField(null=True, blank=True)
    tested_by = models.UUIDField(null=True, blank=True)

    class Meta:
        db_table = "cymed_lab_sensitivities"
        unique_together = [("organism", "antibiotic_code")]


class ResistanceProfile(BaseModel):
    """Resistance mechanisms detected in an organism (e.g., MRSA, ESBL, CRE)."""

    RESISTANCE_MECHANISMS = [
        ("mrsa", "MRSA â€” Methicillin-Resistant S. aureus"),
        ("esbl", "ESBL â€” Extended-Spectrum Beta-Lactamase"),
        ("cre", "CRE â€” Carbapenem-Resistant Enterobacteriaceae"),
        ("vrsa", "VRSA â€” Vancomycin-Resistant S. aureus"),
        ("vre", "VRE â€” Vancomycin-Resistant Enterococcus"),
        ("mdr", "MDR â€” Multi-Drug Resistant"),
        ("xdr", "XDR â€” Extensively Drug Resistant"),
        ("pan_resistant", "PDR â€” Pan-Drug Resistant"),
        ("other", "Other Resistance Mechanism"),
    ]

    organism = models.ForeignKey(
        Organism, on_delete=models.CASCADE, related_name="resistance_profiles"
    )
    resistance_mechanism = models.CharField(max_length=30, choices=RESISTANCE_MECHANISMS)
    confirmed = models.BooleanField(default=False)
    detection_method = models.CharField(max_length=100, blank=True)
    detected_at = models.DateTimeField(null=True, blank=True)
    reported_to_infection_control = models.BooleanField(default=False)
    outbreak_flagged = models.BooleanField(default=False)

    class Meta:
        db_table = "cymed_lab_resistance_profiles"


class MicrobiologyResult(BaseModel):
    """Final interpretive report for a microbiology order item."""

    order_item = models.OneToOneField(
        "lab_orders.LabOrderItem", on_delete=models.CASCADE, related_name="microbiology_result"
    )
    final_interpretation = models.TextField()
    clinical_notes = models.TextField(blank=True)
    reported_by = models.UUIDField()
    reported_at = models.DateTimeField(auto_now_add=True)
    reviewed_by = models.UUIDField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    fhir_diagnostic_report_id = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "cymed_lab_microbiology_results"
