"""
Assessment: the student-facing submission + quiz engine.

This is deliberately *not* a second gradebook. `cyed_gradebook.Assessment` is the
teacher-side mark record (max_score / weight / curriculum_code / due_date) and
`cyed_gradebook.Grade` is the mark itself. This app owns everything the student
actually touches — the assignment brief, their submission, the quiz, their
attempt and answers — and it *feeds* gradebook.Grade when an Assignment is
linked to a gradebook.Assessment (see services.sync_gradebook_grade).

Uploads follow the same in-row approach as products/cyed/intake (BinaryField +
content_type), so no object-store dependency is introduced here.
"""

from datetime import timedelta
from decimal import Decimal

from django.db import models
from django.utils import timezone

from platform.common.models import BaseModel

# ── Vocabulary shared with services.py and views.py ──────────────────────────
KIND_MULTIPLE_CHOICE = "multiple_choice"
KIND_MULTI_SELECT = "multi_select"
KIND_TRUE_FALSE = "true_false"
KIND_SHORT_ANSWER = "short_answer"
KIND_ESSAY = "essay"

#: Kinds the engine can mark without a human. `essay` is deliberately absent.
AUTO_GRADED_KINDS = frozenset(
    {KIND_MULTIPLE_CHOICE, KIND_MULTI_SELECT, KIND_TRUE_FALSE, KIND_SHORT_ANSWER}
)
#: Kinds whose answer is a selection of Choice rows (i.e. have an answer key).
CHOICE_KINDS = frozenset({KIND_MULTIPLE_CHOICE, KIND_MULTI_SELECT, KIND_TRUE_FALSE})


class Assignment(BaseModel):
    """
    A piece of work set for a class. May hang off an LMS lesson, and may be
    linked to a gradebook.Assessment — that link is what makes grading a
    submission write back into the gradebook.
    """

    class_section = models.ForeignKey(
        "cyed_sis.ClassSection", on_delete=models.CASCADE, related_name="assignments"
    )
    lesson = models.ForeignKey(
        "cyed_lms.Lesson", on_delete=models.SET_NULL, null=True, blank=True, related_name="assignments"
    )
    assessment = models.ForeignKey(
        "cyed_gradebook.Assessment",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assignments",
        help_text="Link to the gradebook mark record. When set, grading a submission writes a Grade.",
    )
    title = models.CharField(max_length=255)
    instructions = models.TextField(blank=True)
    due_at = models.DateTimeField(null=True, blank=True)
    max_score = models.DecimalField(max_digits=7, decimal_places=2, default=Decimal("100"))
    allow_late = models.BooleanField(default=False)
    # ACARA content-description code (e.g. AC9M8N01).
    curriculum_code = models.CharField(max_length=50, blank=True)
    is_published = models.BooleanField(default=False)

    class Meta:
        db_table = "cyed_assignments"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["tenant_id", "class_section"], name="idx_assignment_tenant_sec"),
        ]

    def __str__(self):
        return self.title

    @property
    def is_overdue(self) -> bool:
        return bool(self.due_at and timezone.now() > self.due_at)

    def accepts_submission_at(self, when=None) -> bool:
        """False only when the deadline has passed and late work is not allowed."""
        when = when or timezone.now()
        if not self.due_at or when <= self.due_at:
            return True
        return self.allow_late


class Submission(BaseModel):
    """One student's attempt at one Assignment."""

    DRAFT = "draft"
    SUBMITTED = "submitted"
    LATE = "late"
    GRADED = "graded"
    RETURNED = "returned"
    STATUS = [
        (DRAFT, "Draft"),
        (SUBMITTED, "Submitted"),
        (LATE, "Submitted Late"),
        (GRADED, "Graded"),
        (RETURNED, "Returned to Student"),
    ]
    #: Statuses meaning "the student has handed this in".
    HANDED_IN = frozenset({SUBMITTED, LATE, GRADED, RETURNED})

    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name="submissions")
    student = models.ForeignKey(
        "cyed_sis.Student", on_delete=models.CASCADE, related_name="assignment_submissions"
    )
    submitted_at = models.DateTimeField(null=True, blank=True)
    text_response = models.TextField(blank=True)
    # Upload, stored in-row exactly as products/cyed/intake.DocumentIntake does.
    file_bytes = models.BinaryField(null=True, blank=True)
    file_name = models.CharField(max_length=255, blank=True)
    content_type = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default=DRAFT)
    attempt_number = models.PositiveSmallIntegerField(default=1)
    score = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)
    feedback = models.TextField(blank=True)
    graded_by = models.CharField(max_length=255, blank=True)
    graded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "cyed_assignment_submissions"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant_id", "assignment", "student", "attempt_number"],
                name="uniq_submission_per_student_attempt",
            )
        ]
        indexes = [
            models.Index(fields=["tenant_id", "assignment"], name="idx_submission_tenant_asgn"),
        ]

    def __str__(self):
        return f"{self.student_id} → {self.assignment_id} ({self.status})"

    @property
    def is_handed_in(self) -> bool:
        return self.status in self.HANDED_IN

    @property
    def has_file(self) -> bool:
        return bool(self.file_bytes)

    @property
    def percentage(self):
        if self.score is None or not self.assignment.max_score:
            return None
        return round(float(self.score) / float(self.assignment.max_score) * 100, 1)


class Quiz(BaseModel):
    """A timed, auto-marked set of questions."""

    class_section = models.ForeignKey(
        "cyed_sis.ClassSection", on_delete=models.CASCADE, related_name="quizzes"
    )
    lesson = models.ForeignKey(
        "cyed_lms.Lesson", on_delete=models.SET_NULL, null=True, blank=True, related_name="quizzes"
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    time_limit_minutes = models.PositiveSmallIntegerField(
        null=True, blank=True, help_text="Null means untimed."
    )
    max_attempts = models.PositiveSmallIntegerField(default=1)
    is_published = models.BooleanField(default=False)
    shuffle_questions = models.BooleanField(default=False)
    curriculum_code = models.CharField(max_length=50, blank=True)

    class Meta:
        db_table = "cyed_quizzes"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["tenant_id", "class_section"], name="idx_quiz_tenant_sec"),
        ]

    def __str__(self):
        return self.title

    @property
    def total_points(self) -> Decimal:
        return sum((q.points for q in self.questions.all()), Decimal("0"))


class Question(BaseModel):
    KIND_CHOICES = [
        (KIND_MULTIPLE_CHOICE, "Multiple Choice (one correct)"),
        (KIND_MULTI_SELECT, "Multi-Select (several correct)"),
        (KIND_TRUE_FALSE, "True / False"),
        (KIND_SHORT_ANSWER, "Short Answer"),
        (KIND_ESSAY, "Extended Response (human-marked)"),
    ]

    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="questions")
    text = models.TextField()
    kind = models.CharField(max_length=20, choices=KIND_CHOICES, default=KIND_MULTIPLE_CHOICE)
    points = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal("1"))
    sequence = models.PositiveSmallIntegerField(default=1)
    # Answer key for short_answer. NEVER serialise this to a student.
    accepted_answers = models.JSONField(default=list, blank=True)

    class Meta:
        db_table = "cyed_quiz_questions"
        ordering = ["sequence", "created_at"]

    def __str__(self):
        return f"Q{self.sequence}: {self.text[:60]}"

    @property
    def is_auto_graded(self) -> bool:
        return self.kind in AUTO_GRADED_KINDS


class Choice(BaseModel):
    """
    An option for a choice-based Question. `is_correct` is the answer key and is
    stripped from every student-facing serializer (see serializers.py).
    """

    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="choices")
    text = models.CharField(max_length=500)
    is_correct = models.BooleanField(default=False)
    sequence = models.PositiveSmallIntegerField(default=1)

    class Meta:
        db_table = "cyed_quiz_choices"
        ordering = ["sequence", "created_at"]

    def __str__(self):
        return self.text[:60]


class QuizAttempt(BaseModel):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="attempts")
    student = models.ForeignKey(
        "cyed_sis.Student", on_delete=models.CASCADE, related_name="quiz_attempts"
    )
    started_at = models.DateTimeField(default=timezone.now)
    submitted_at = models.DateTimeField(null=True, blank=True)
    score = models.DecimalField(max_digits=7, decimal_places=2, default=Decimal("0"))
    max_score = models.DecimalField(max_digits=7, decimal_places=2, default=Decimal("0"))
    is_graded = models.BooleanField(default=False)
    attempt_number = models.PositiveSmallIntegerField(default=1)

    class Meta:
        db_table = "cyed_quiz_attempts"
        ordering = ["-started_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant_id", "quiz", "student", "attempt_number"],
                name="uniq_attempt_per_student_quiz",
            )
        ]
        indexes = [
            models.Index(fields=["tenant_id", "quiz"], name="idx_attempt_tenant_quiz"),
        ]

    def __str__(self):
        return f"{self.student_id} · {self.quiz_id} #{self.attempt_number}"

    @property
    def expires_at(self):
        if not self.quiz.time_limit_minutes:
            return None
        return self.started_at + timedelta(minutes=self.quiz.time_limit_minutes)

    @property
    def is_expired(self) -> bool:
        expiry = self.expires_at
        return bool(expiry and self.submitted_at is None and timezone.now() > expiry)

    @property
    def percentage(self):
        if not self.max_score:
            return None
        return round(float(self.score) / float(self.max_score) * 100, 1)


class Answer(BaseModel):
    attempt = models.ForeignKey(QuizAttempt, on_delete=models.CASCADE, related_name="answers")
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="answers")
    selected_choices = models.ManyToManyField(Choice, blank=True, related_name="answers")
    text_answer = models.TextField(blank=True)
    # Null means "not marked yet" — an unmarked essay, not a zero.
    awarded_points = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    is_correct = models.BooleanField(null=True, blank=True)

    class Meta:
        db_table = "cyed_quiz_answers"
        ordering = ["question__sequence", "created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant_id", "attempt", "question"], name="uniq_answer_per_attempt_question"
            )
        ]

    def __str__(self):
        return f"{self.attempt_id} · {self.question_id}"
