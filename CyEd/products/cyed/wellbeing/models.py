from datetime import timedelta

from django.db import models
from django.utils import timezone

from core.crypto import EncryptedTextField
from platform.common.models import BaseModel
from products.cyed.sis.models import Student


class LearnerProfile(BaseModel):
    """
    Support profile driving the Adaptive & Special-Needs AI (capability #4).
    Accommodations, EAL/D phase, and modality prefs are stored as data so the
    adaptive engine applies them consistently and auditably.
    """

    # Australian Curriculum EAL/D phases: Beginning / Emerging / Developing / Consolidating.
    EALD_CHOICES = [
        ("", "Not EAL/D"),
        ("BL", "Beginning"),
        ("EM", "Emerging"),
        ("DV", "Developing"),
        ("CO", "Consolidating"),
    ]

    student = models.OneToOneField(Student, on_delete=models.CASCADE, related_name="learner_profile")
    eald_level = models.CharField(max_length=2, choices=EALD_CHOICES, blank=True, default="")
    first_language = models.CharField(max_length=100, blank=True)
    is_neurodivergent = models.BooleanField(default=False)
    # Free-form list/JSON of accommodations (e.g. extra time, chunked tasks).
    accommodations = models.TextField(blank=True)
    reading_level = models.CharField(max_length=50, blank=True)
    preferred_modalities = models.CharField(max_length=255, blank=True)  # e.g. "visual,audio"
    has_individual_plan = models.BooleanField(default=False)  # IEP / ILP flag
    notes = EncryptedTextField(blank=True)

    class Meta:
        db_table = "cyed_learner_profiles"
        ordering = ["-created_at"]

    def __str__(self):
        return f"LearnerProfile({self.student_id})"


class BehaviourIncident(BaseModel):
    CATEGORY_CHOICES = [
        ("positive", "Positive Recognition"),
        ("minor", "Minor"),
        ("major", "Major"),
    ]

    # Default point values by category, used when none is given explicitly.
    # Positive recognition earns merits; misconduct costs demerits. Schools
    # tune the magnitudes, so these are defaults rather than fixed rules.
    DEFAULT_POINTS = {"positive": 1, "minor": -1, "major": -3}

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="behaviour_incidents")
    date = models.DateField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default="minor")
    description = models.TextField(blank=True)
    action_taken = models.TextField(blank=True)
    reported_by = models.CharField(max_length=255, blank=True)
    resolved = models.BooleanField(default=False)
    # Signed: positive earns, negative costs. Stored rather than derived from
    # `category` so a school can weight one incident more heavily than another
    # without inventing a new category for every magnitude.
    points = models.SmallIntegerField(default=0)
    # Merits are meant to be seen. A house/tutor group scoreboard is the point
    # of a merit system, and it needs somewhere to aggregate to.
    house = models.CharField(max_length=100, blank=True)

    class Meta:
        db_table = "cyed_behaviour_incidents"
        ordering = ["-date"]
        indexes = [
            models.Index(fields=["tenant_id", "student", "date"], name="idx_behaviour_student_date"),
        ]

    def save(self, *args, **kwargs):
        # Only fill in on first write: a hand-adjusted value must survive an
        # edit to the description.
        if self._state.adding and not self.points:
            self.points = self.DEFAULT_POINTS.get(self.category, 0)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student_id} · {self.category} · {self.date}"


class WellbeingCheckIn(BaseModel):
    """
    Optional student socio-emotional check-in. Sentiment is computed on save
    (transparent lexicon); `flagged` items surface to pastoral staff. Screening
    aid only — a human always reviews.
    """

    MOOD_CHOICES = [
        ("great", "Great"), ("ok", "OK"), ("low", "Low"), ("struggling", "Struggling"),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="checkins")
    date = models.DateField(null=True, blank=True)
    mood = models.CharField(max_length=20, choices=MOOD_CHOICES, blank=True)
    response_text = EncryptedTextField(blank=True)
    sentiment_score = models.DecimalField(max_digits=4, decimal_places=3, default=0)
    sentiment_label = models.CharField(max_length=20, blank=True)
    flagged = models.BooleanField(default=False)

    class Meta:
        db_table = "cyed_wellbeing_checkins"
        ordering = ["-created_at"]

    def __str__(self):
        return f"CheckIn({self.student_id} · {self.sentiment_label})"


class WellbeingNote(BaseModel):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="wellbeing_notes")
    date = models.DateField()
    category = models.CharField(max_length=100, blank=True)
    note = EncryptedTextField(blank=True)
    is_confidential = models.BooleanField(default=True)
    author = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "cyed_wellbeing_notes"
        ordering = ["-date"]

    def __str__(self):
        return f"WellbeingNote({self.student_id} · {self.date})"


class SupportPlan(BaseModel):
    """
    An individual education plan (IEP / ILP / personalised learning plan).

    `LearnerProfile.has_individual_plan` was a boolean. It said a plan existed
    somewhere — on a shared drive, in a folder — and proved nothing. NCCD
    requires *evidence* that adjustments were planned, provided and reviewed,
    and a tickbox is the one thing an auditor cannot accept.

    The structure follows what that evidence has to show:

    * **Adjustments** are what the school actually does differently, each
      mapped to an NCCD level, so the annual return is derived from the plan
      rather than typed in beside it and left to drift.
    * **Goals** are what the adjustments are for, with progress recorded
      against them — an adjustment nobody can say worked is not evidence.
    * **Reviews** are dated meetings with named participants. "Reviewed
      annually" with no meeting behind it is the gap schools get pulled up on.

    Plans are versioned by supersession rather than edited in place: a plan
    that changed silently cannot show what was in force last March, which is
    exactly the question asked when something has gone wrong.
    """

    PLAN_TYPES = [
        ("iep", "Individual Education Plan"),
        ("ilp", "Individual Learning Plan"),
        ("behaviour", "Behaviour Support Plan"),
        ("risk", "Risk Management Plan"),
        ("eald", "EAL/D Support Plan"),
    ]
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("active", "Active"),
        ("superseded", "Superseded"),
        ("closed", "Closed"),
    ]
    # A plan inside this window is surfaced for review. Roughly the notice a
    # coordinator needs to convene a meeting with a family.
    REVIEW_WARNING_DAYS = 45

    student = models.ForeignKey(
        Student, on_delete=models.CASCADE, related_name="support_plans"
    )
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPES, default="iep")
    title = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")

    start_date = models.DateField(null=True, blank=True)
    review_due = models.DateField(null=True, blank=True)

    # Why the plan exists. Encrypted: disability and health information.
    strengths = EncryptedTextField(blank=True)
    needs = EncryptedTextField(blank=True)
    # Consultation is required under the Disability Standards and is the first
    # thing an auditor asks about.
    family_consulted_on = models.DateField(null=True, blank=True)
    student_voice = EncryptedTextField(blank=True)

    coordinator = models.ForeignKey(
        "cyed_hr.Staff", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="coordinated_support_plans",
    )
    superseded_by = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="supersedes",
    )
    closed_on = models.DateField(null=True, blank=True)
    closed_reason = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "cyed_support_plans"
        ordering = ["-start_date", "-created_at"]
        indexes = [
            models.Index(
                fields=["tenant_id", "status", "review_due"],
                name="idx_support_plan_review",
            ),
        ]

    def review_state(self, as_at=None) -> str:
        as_at = as_at or timezone.localdate()
        if self.status != "active":
            return self.status
        if self.review_due is None:
            return "no_review_date"
        if self.review_due < as_at:
            return "overdue"
        if self.review_due <= as_at + timedelta(days=self.REVIEW_WARNING_DAYS):
            return "due_soon"
        return "current"

    def highest_adjustment(self) -> str:
        """
        The most intensive adjustment in the plan — what the NCCD return
        reports for this student, derived rather than re-entered.
        """
        order = ["qdtp", "supplementary", "substantial", "extensive"]
        levels = [a.nccd_level for a in self.adjustments.all() if a.nccd_level]
        if not levels:
            return ""
        return max(levels, key=order.index)

    def __str__(self):
        return f"{self.get_plan_type_display()} for {self.student_id} ({self.status})"


class SupportAdjustment(BaseModel):
    """
    One thing the school does differently for this student.

    `nccd_level` is the evidence link: the annual return is derived from the
    adjustments actually recorded here, so a school cannot report "substantial"
    while its plan describes nothing beyond ordinary teaching.
    """

    CATEGORY_CHOICES = [
        ("curriculum", "Curriculum"),
        ("instruction", "Instruction"),
        ("environment", "Environment"),
        ("assessment", "Assessment"),
        ("personal_care", "Personal care"),
        ("safety", "Safety"),
        ("communication", "Communication"),
    ]
    NCCD_LEVELS = [
        ("qdtp", "Quality differentiated teaching practice"),
        ("supplementary", "Supplementary"),
        ("substantial", "Substantial"),
        ("extensive", "Extensive"),
    ]

    plan = models.ForeignKey(
        SupportPlan, on_delete=models.CASCADE, related_name="adjustments"
    )
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES)
    description = models.TextField(
        help_text="What is done differently — concrete enough for a relief teacher to follow."
    )
    nccd_level = models.CharField(max_length=20, choices=NCCD_LEVELS, blank=True)
    # An adjustment with nobody responsible does not happen.
    responsible = models.CharField(max_length=255, blank=True)
    frequency = models.CharField(max_length=150, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "cyed_support_adjustments"
        ordering = ["category"]

    def __str__(self):
        return f"{self.get_category_display()}: {self.description[:40]}"


class SupportGoal(BaseModel):
    """
    What the adjustments are meant to achieve, and whether they did.

    Progress is recorded against the goal because an adjustment nobody can say
    worked is not evidence of anything.
    """

    PROGRESS_CHOICES = [
        ("not_started", "Not started"),
        ("working_towards", "Working towards"),
        ("achieved", "Achieved"),
        ("discontinued", "Discontinued"),
    ]

    plan = models.ForeignKey(SupportPlan, on_delete=models.CASCADE, related_name="goals")
    description = models.TextField()
    success_criteria = models.TextField(
        blank=True, help_text="How the school will know it has been met."
    )
    target_date = models.DateField(null=True, blank=True)
    progress = models.CharField(max_length=20, choices=PROGRESS_CHOICES, default="not_started")
    progress_note = models.TextField(blank=True)
    progress_updated_on = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "cyed_support_goals"
        ordering = ["target_date", "created_at"]

    def __str__(self):
        return f"{self.description[:50]} ({self.progress})"


class SupportPlanReview(BaseModel):
    """
    A dated review meeting with named participants.

    Recording who was in the room — particularly whether the family was — is
    the evidence the Disability Standards actually ask for, and the thing
    "reviewed annually" on its own cannot supply.
    """

    plan = models.ForeignKey(SupportPlan, on_delete=models.CASCADE, related_name="reviews")
    held_on = models.DateField()
    participants = models.CharField(
        max_length=500, help_text="Everyone present, including the family."
    )
    family_present = models.BooleanField(default=False)
    student_present = models.BooleanField(default=False)
    discussion = EncryptedTextField(blank=True)
    outcome = models.CharField(max_length=500, blank=True)
    next_review_due = models.DateField(null=True, blank=True)
    recorded_by = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "cyed_support_plan_reviews"
        ordering = ["-held_on"]

    def __str__(self):
        return f"Review of {self.plan_id} on {self.held_on}"
