from decimal import Decimal

from django.db import models

from platform.common.models import BaseModel
from products.cyed.sis.models import ClassSection, Student


class Rubric(BaseModel):
    """
    A marking rubric: criteria, each with performance levels worth marks.

    Teachers mark against criteria, not a single number — "17 out of 20" tells
    a student nothing, and a teacher justifying a grade to a parent needs the
    breakdown. CyEd had no structure for this at all.

    Rubrics are reusable across assessments because a school's "Extended
    response" rubric is the same one every term, and re-typing it is how four
    slightly different versions end up in circulation.
    """

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    subject = models.CharField(max_length=100, blank=True)
    year_level = models.PositiveSmallIntegerField(null=True, blank=True)
    # ACARA achievement standard this rubric assesses against, when it maps to
    # one. Free text: state frameworks use their own codes.
    curriculum_code = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "cyed_rubrics"
        ordering = ["name"]

    def total_marks(self):
        """The rubric's ceiling — the sum of each criterion's best level."""
        from decimal import Decimal

        total = Decimal("0")
        for criterion in self.criteria.all():
            best = max(
                (level.marks for level in criterion.levels.all()), default=Decimal("0")
            )
            total += Decimal(best) * Decimal(criterion.weight)
        return total

    def __str__(self):
        return self.name


class RubricCriterion(BaseModel):
    """One thing being judged — "Structure and organisation", "Use of evidence"."""

    rubric = models.ForeignKey(Rubric, on_delete=models.CASCADE, related_name="criteria")
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    # Some criteria matter more. Multiplies the level's marks rather than
    # forcing the levels themselves to carry uneven numbers, which is what
    # makes a rubric hard to read.
    weight = models.DecimalField(max_digits=4, decimal_places=2, default=1)
    sequence = models.PositiveSmallIntegerField(default=1)

    class Meta:
        db_table = "cyed_rubric_criteria"
        ordering = ["sequence", "name"]

    def __str__(self):
        return self.name


class RubricLevel(BaseModel):
    """
    One performance band on a criterion, with what it looks like and what it
    is worth.

    The descriptor is the part that does the work: a level called "Good" with
    no description is a number in disguise, and two teachers will not agree on
    what it means.
    """

    criterion = models.ForeignKey(
        RubricCriterion, on_delete=models.CASCADE, related_name="levels"
    )
    label = models.CharField(max_length=100)
    descriptor = models.TextField(
        help_text="What work at this level actually looks like."
    )
    marks = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    # A–E where the school reports that way, so a rubric mark can roll into a
    # report card without a second judgement.
    achievement_level = models.CharField(max_length=5, blank=True)
    sequence = models.PositiveSmallIntegerField(default=1)

    class Meta:
        db_table = "cyed_rubric_levels"
        ordering = ["criterion", "-marks"]
        constraints = [
            models.UniqueConstraint(
                fields=["criterion", "label"], name="uniq_level_label_per_criterion"
            ),
        ]

    def __str__(self):
        return f"{self.label} ({self.marks})"


class Assessment(BaseModel):
    TYPE_CHOICES = [
        ("formative", "Formative"),
        ("summative", "Summative"),
        ("assignment", "Assignment"),
        ("exam", "Exam"),
    ]

    class_section = models.ForeignKey(
        ClassSection, on_delete=models.CASCADE, related_name="assessments"
    )
    name = models.CharField(max_length=255)
    assessment_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default="assignment")
    max_score = models.DecimalField(max_digits=7, decimal_places=2, default=100)
    weight = models.DecimalField(max_digits=5, decimal_places=2, default=1)
    # ACARA content-description code this assessment maps to (e.g. AC9M8N01).
    curriculum_code = models.CharField(max_length=50, blank=True)
    due_date = models.DateField(null=True, blank=True)
    # Optional: an assessment marked against a rubric derives its score from
    # the per-criterion judgements rather than a typed-in total.
    rubric = models.ForeignKey(
        Rubric, on_delete=models.SET_NULL, null=True, blank=True, related_name="assessments"
    )

    class Meta:
        db_table = "cyed_assessments"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.class_section_id})"


class Grade(BaseModel):
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name="grades")
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="grades")
    score = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)
    comment = models.TextField(blank=True)
    # Achievement level against the standard (A–E in the Australian Curriculum).
    achievement_level = models.CharField(max_length=5, blank=True)

    class Meta:
        db_table = "cyed_grades"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["assessment", "student"], name="uniq_grade_per_student_assessment"
            )
        ]

    def __str__(self):
        return f"{self.student_id} · {self.assessment_id}: {self.score}"

    @property
    def percentage(self):
        if self.score is None or not self.assessment.max_score:
            return None
        return round(float(self.score) / float(self.assessment.max_score) * 100, 1)


class RubricMark(BaseModel):
    """
    The level a teacher chose for one criterion, for one student.

    Stored per criterion rather than collapsed into the total, because the
    breakdown *is* the feedback — it is what a student reads to know what to do
    differently, and what a teacher shows a parent who disputes a grade.
    """

    grade = models.ForeignKey(
        Grade, on_delete=models.CASCADE, related_name="rubric_marks"
    )
    criterion = models.ForeignKey(
        RubricCriterion, on_delete=models.CASCADE, related_name="judgements"
    )
    # Not `marks`: that is already the mark value on RubricLevel, and the
    # reverse accessor would shadow it.
    level = models.ForeignKey(
        RubricLevel, on_delete=models.PROTECT, related_name="awarded_to"
    )
    comment = models.TextField(blank=True)

    class Meta:
        db_table = "cyed_rubric_marks"
        ordering = ["criterion__sequence"]
        constraints = [
            # One judgement per criterion. Two would make the total ambiguous.
            models.UniqueConstraint(
                fields=["grade", "criterion"], name="uniq_mark_per_criterion_per_grade"
            ),
        ]

    def weighted_marks(self):
        return Decimal(self.level.marks) * Decimal(self.criterion.weight)

    def __str__(self):
        return f"{self.criterion.name}: {self.level.label}"
