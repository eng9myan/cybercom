from django.db import models

from platform.common.models import BaseModel


class AgentDefinition(BaseModel):
    """
    Registry entry for a CyEd GenAI capability. Mirrors the cyai_platform
    AgentDefinition concept, scoped to education agents. Privacy-first flags
    (no_train, human_in_the_loop, grounding) encode the Australian Framework
    for Generative AI in Schools requirements as data, not promises.
    """

    CAPABILITY_CHOICES = [
        ("tutor", "Curriculum-Aligned Learning Assistant"),
        ("lesson_planner", "Lesson Plan Generator"),
        ("rubric", "Rubric Generator"),
        ("differentiator", "Differentiated Task Generator"),
        ("integrity", "Academic Integrity / Authenticity"),
        ("adaptive", "Adaptive / Special-Needs Support"),
    ]

    key = models.CharField(max_length=100)  # e.g. "cyed.tutor"
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    capability = models.CharField(max_length=30, choices=CAPABILITY_CHOICES, default="tutor")
    model_name = models.CharField(max_length=100, default="claude-sonnet-5")
    # Curriculum authority the agent is grounded in (RAG source), e.g. ACARA.
    grounding = models.CharField(max_length=100, blank=True, default="ACARA")
    no_train = models.BooleanField(default=True)  # student inputs never used for training
    human_in_the_loop = models.BooleanField(default=True)  # outputs routed to HITL review
    data_residency = models.CharField(max_length=20, default="AU")
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "cyed_agent_definitions"
        ordering = ["key"]
        constraints = [
            models.UniqueConstraint(fields=["tenant_id", "key"], name="uniq_agent_key_per_tenant")
        ]

    def __str__(self):
        return f"{self.key} ({self.capability})"


class AgentInteractionLog(BaseModel):
    """
    Transparency/accountability trail for every AI interaction (Framework
    principles: Transparency, Accountability). Student inputs are tenant-scoped
    and retention-windowed; never used for model training.
    """

    agent = models.ForeignKey(AgentDefinition, on_delete=models.CASCADE, related_name="interactions")
    actor = models.CharField(max_length=255, blank=True)  # teacher/student identifier
    prompt_summary = models.CharField(max_length=500, blank=True)
    curriculum_code = models.CharField(max_length=50, blank=True)
    reviewed_by_human = models.BooleanField(default=False)

    class Meta:
        db_table = "cyed_agent_interaction_logs"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.agent_id} @ {self.created_at:%Y-%m-%d}"


class GeneratedArtifact(BaseModel):
    """
    Output of a teacher-tool agent (lesson plan / rubric / differentiated task).
    Always created as `pending_review` — this IS the human-in-the-loop queue:
    a teacher approves or rejects before the artifact is usable. Grounded to
    ACARA via `curriculum_codes`.
    """

    ARTIFACT_TYPES = [
        ("lesson_plan", "Lesson Plan"),
        ("rubric", "Rubric"),
        ("differentiated_task", "Differentiated Task"),
    ]
    STATUS_CHOICES = [
        ("pending_review", "Pending Review"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]

    agent = models.ForeignKey(AgentDefinition, on_delete=models.CASCADE, related_name="artifacts")
    artifact_type = models.CharField(max_length=30, choices=ARTIFACT_TYPES)
    title = models.CharField(max_length=255)
    subject = models.CharField(max_length=100, blank=True)
    year_level = models.PositiveSmallIntegerField(null=True, blank=True)
    curriculum_codes = models.CharField(max_length=255, blank=True)  # comma-separated ACARA codes
    content = models.JSONField(default=dict)  # structured plan/rubric/tasks
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending_review")
    generated_by = models.CharField(max_length=255, blank=True)
    reviewed_by = models.CharField(max_length=255, blank=True)
    review_note = models.TextField(blank=True)
    llm_generated = models.BooleanField(default=False)  # False = grounded extractive fallback

    class Meta:
        db_table = "cyed_generated_artifacts"
        ordering = ["-created_at"]

    def approve(self, reviewer="", note=""):
        self.status = "approved"
        self.reviewed_by = reviewer
        self.review_note = note
        self.save(update_fields=["status", "reviewed_by", "review_note", "updated_at"])

    def reject(self, reviewer="", note=""):
        self.status = "rejected"
        self.reviewed_by = reviewer
        self.review_note = note
        self.save(update_fields=["status", "reviewed_by", "review_note", "updated_at"])

    def __str__(self):
        return f"{self.artifact_type}: {self.title} ({self.status})"


class IntegrityReview(BaseModel):
    """
    Academic-integrity / authenticity review — evaluates *process provenance*,
    never a text classifier. A computed `risk_band` only flags work for a human;
    the `decision` is always made by a person (never auto-accuses). Disclosed AI
    use is treated as compliance, not misconduct.
    """

    RISK_CHOICES = [("low", "Low"), ("medium", "Medium"), ("high", "High")]
    DECISION_CHOICES = [
        ("pending", "Pending Human Review"),
        ("cleared", "Cleared"),
        ("concern", "Concern Noted"),
        ("escalated", "Escalated"),
    ]

    student = models.ForeignKey(
        "cyed_sis.Student", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="integrity_reviews",
    )
    title = models.CharField(max_length=255)
    assessment_ref = models.CharField(max_length=255, blank=True)
    # Process-provenance evidence (NOT content analysis):
    draft_versions = models.PositiveSmallIntegerField(default=0)
    edit_span_minutes = models.PositiveIntegerField(default=0)  # first → last edit
    paste_events = models.PositiveSmallIntegerField(default=0)
    large_paste_events = models.PositiveSmallIntegerField(default=0)  # pastes over a threshold
    disclosed_ai_use = models.BooleanField(default=False)
    ai_disclosure_note = models.TextField(blank=True)
    # Computed flag (advisory only):
    risk_band = models.CharField(max_length=10, choices=RISK_CHOICES, default="low")
    signals = models.JSONField(default=dict)
    # Human decision (authoritative):
    decision = models.CharField(max_length=20, choices=DECISION_CHOICES, default="pending")
    decided_by = models.CharField(max_length=255, blank=True)
    decision_note = models.TextField(blank=True)

    class Meta:
        db_table = "cyed_integrity_reviews"
        ordering = ["-created_at"]

    def decide(self, decision, decided_by="", note=""):
        self.decision = decision
        self.decided_by = decided_by
        self.decision_note = note
        self.save(update_fields=["decision", "decided_by", "decision_note", "updated_at"])

    def __str__(self):
        return f"IntegrityReview({self.title}): {self.risk_band}/{self.decision}"
