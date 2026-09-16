from django.db import models

from platform.common.models import BaseModel


class GeneralCapability(BaseModel):
    """
    An ACARA v9 General Capability — Critical and Creative Thinking (CCT),
    Digital Literacy (DL), Ethical Understanding (EU), Intercultural
    Understanding (IU), Literacy (L), Numeracy (N), Personal and Social
    Capability (PSC).

    General capabilities are *many-to-many* against content descriptions: one
    content description can develop several capabilities and one capability is
    developed by thousands of content descriptions. That relationship cannot be
    expressed as a column on CurriculumOutcome, hence a first-class model.
    """

    code = models.CharField(max_length=20)  # e.g. "CCT"
    name = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    framework = models.CharField(max_length=50, default="ACARA v9")
    source_uri = models.CharField(max_length=500, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "cyed_curriculum_general_capabilities"
        ordering = ["code"]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant_id", "code", "framework"], name="uniq_gencap_code_framework"
            )
        ]

    def __str__(self):
        return f"{self.code} — {self.name}" if self.name else self.code


class CrossCurriculumPriority(BaseModel):
    """
    An ACARA v9 Cross-Curriculum Priority — Sustainability (S), Aboriginal and
    Torres Strait Islander Histories and Cultures, Asia and Australia's
    Engagement with Asia. Same many-to-many shape as GeneralCapability.
    """

    code = models.CharField(max_length=20)  # e.g. "S"
    name = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    framework = models.CharField(max_length=50, default="ACARA v9")
    source_uri = models.CharField(max_length=500, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "cyed_curriculum_cross_curriculum_priorities"
        ordering = ["code"]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant_id", "code", "framework"], name="uniq_ccp_code_framework"
            )
        ]

    def __str__(self):
        return f"{self.code} — {self.name}" if self.name else self.code


class AchievementStandard(BaseModel):
    """
    The achievement standard for one (learning area, year level) pair.

    ACARA publishes ONE achievement standard per learning area per year level,
    shared by every content description at that level. Storing it as a text
    column on CurriculumOutcome duplicated it across hundreds of rows and made
    it impossible to update in one place — this model is the normalised form.
    CurriculumOutcome.achievement_standard (text) is retained for back-compat.
    """

    learning_area = models.CharField(max_length=100)
    subject = models.CharField(max_length=100, blank=True)
    year_level = models.PositiveSmallIntegerField(default=0)  # 0 = Foundation
    standard_text = models.TextField(blank=True)
    framework = models.CharField(max_length=50, default="ACARA v9")
    source_uri = models.CharField(max_length=500, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "cyed_curriculum_achievement_standards"
        ordering = ["learning_area", "year_level"]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant_id", "learning_area", "subject", "year_level", "framework"],
                name="uniq_achievement_standard_area_year",
            )
        ]

    def __str__(self):
        return f"{self.learning_area} Y{self.year_level} achievement standard"


class CurriculumOutcome(BaseModel):
    """
    A single curriculum content description / achievement standard — the ACARA
    (Australian Curriculum) dataset, tenant-scoped like a terminology registry.
    The `code` (e.g. AC9M8N01) is what assessments, lesson plans, and the RAG
    tutor ground against. `framework`/`state` allow state variants (NESA/VCAA).

    MRAC (Machine-Readable Australian Curriculum) additions:
      * `is_elaboration` + `parent_outcome` — an elaboration such as AC9M7N06_E1
        is its own statement in MRAC but hangs off the base content description.
      * `general_capabilities` / `cross_curriculum_priorities` — the real M2M
        links MRAC expresses as SKOS references.
      * `achievement_standard_ref` — the normalised achievement standard.
    """

    code = models.CharField(max_length=50)  # e.g. "AC9M8N01"
    learning_area = models.CharField(max_length=100)  # e.g. "Mathematics"
    subject = models.CharField(max_length=100, blank=True)
    year_level = models.PositiveSmallIntegerField(default=0)  # 0 = Foundation
    strand = models.CharField(max_length=150, blank=True)
    sub_strand = models.CharField(max_length=150, blank=True)
    content_description = models.TextField(blank=True)
    achievement_standard = models.TextField(blank=True)
    elaboration = models.TextField(blank=True)
    framework = models.CharField(max_length=50, default="ACARA v9")
    state = models.CharField(max_length=20, blank=True)  # blank = national
    is_active = models.BooleanField(default=True)

    # ── MRAC / ACARA v9 structure ───────────────────────────────────────────
    is_elaboration = models.BooleanField(default=False)
    parent_outcome = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="elaborations",
    )
    achievement_standard_ref = models.ForeignKey(
        AchievementStandard,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="outcomes",
    )
    general_capabilities = models.ManyToManyField(
        GeneralCapability,
        blank=True,
        related_name="outcomes",
        db_table="cyed_curriculum_outcome_general_capabilities",
    )
    cross_curriculum_priorities = models.ManyToManyField(
        CrossCurriculumPriority,
        blank=True,
        related_name="outcomes",
        db_table="cyed_curriculum_outcome_priorities",
    )
    source_uri = models.CharField(max_length=500, blank=True)

    class Meta:
        db_table = "cyed_curriculum_outcomes"
        ordering = ["learning_area", "year_level", "code"]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant_id", "code", "framework"], name="uniq_outcome_code_framework"
            )
        ]

    def __str__(self):
        return f"{self.code} — {self.learning_area} Y{self.year_level}"


class MracImportRun(BaseModel):
    """
    One MRAC ingestion run. Exists so the ACARA CC BY 4.0 attribution notice is
    *stored* alongside the data it covers (a licence condition), and so an
    operator can see what was loaded, from where, and when.
    """

    set_code = models.CharField(max_length=20, blank=True)  # e.g. "LA/MAT"
    source_name = models.CharField(max_length=255, blank=True)  # file name or IRI
    framework = models.CharField(max_length=50, default="ACARA v9")
    statements_seen = models.PositiveIntegerField(default=0)
    outcomes_created = models.PositiveIntegerField(default=0)
    outcomes_updated = models.PositiveIntegerField(default=0)
    elaborations_linked = models.PositiveIntegerField(default=0)
    capability_links = models.PositiveIntegerField(default=0)
    priority_links = models.PositiveIntegerField(default=0)
    standards_upserted = models.PositiveIntegerField(default=0)
    skipped = models.PositiveIntegerField(default=0)
    attribution = models.TextField(blank=True)

    class Meta:
        db_table = "cyed_curriculum_mrac_import_runs"
        ordering = ["-created_at"]

    def __str__(self):
        return f"MRAC {self.set_code or self.source_name} ({self.statements_seen} statements)"
