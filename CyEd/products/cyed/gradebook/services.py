"""
Gradebook bulk operations.

Marking a set of 30 papers meant 30 `POST /gradebook/grades/` requests. Entry
is also the point where a mis-keyed mark does real damage — a score above the
assessment's maximum, or a mark against a student who is not in the class — so
the bulk path validates the whole batch and writes nothing if any row is wrong.

All-or-nothing matters here more than throughput: a partially applied batch
leaves a teacher unable to tell which marks landed, and re-submitting would
double-apply nothing but would still leave them guessing.
"""

from decimal import Decimal, InvalidOperation

from django.db import transaction

from products.cyed.gradebook.models import Grade
from products.cyed.sis.models import Enrolment

GRADE_FIELDS = ("score", "comment", "achievement_level")
# A–E is the Australian Curriculum achievement scale.
ACHIEVEMENT_LEVELS = {"A", "B", "C", "D", "E"}


class GradeError(Exception):
    """The batch was refused for a business reason (→ HTTP 400)."""


def roster_student_ids(class_section_id, tenant_id) -> set:
    return set(
        Enrolment.objects.filter(
            tenant_id=tenant_id, class_section_id=class_section_id, status="active"
        ).values_list("student_id", flat=True)
    )


def _clean_row(row, assessment, roster):
    if not isinstance(row, dict):
        raise GradeError("Each entry in 'grades' must be an object.")
    student_id = row.get("student")
    if not student_id:
        raise GradeError("Each entry in 'grades' needs a 'student'.")
    student_id = str(student_id)

    if roster and student_id not in {str(s) for s in roster}:
        raise GradeError(
            f"Student {student_id} is not enrolled in the class this assessment belongs to."
        )

    score = row.get("score")
    if score not in (None, ""):
        try:
            score = Decimal(str(score))
        except (InvalidOperation, TypeError, ValueError):
            raise GradeError(f"'{row.get('score')}' is not a valid score.")
        if score < 0:
            raise GradeError("A score cannot be negative.")
        # The check that catches a real mistake: 95 entered against an
        # assessment marked out of 20 silently becomes a 475% result and
        # poisons every average that student appears in.
        if assessment.max_score and score > Decimal(assessment.max_score):
            raise GradeError(
                f"Score {score} exceeds the maximum of {assessment.max_score} for "
                f"'{assessment.name}'."
            )
    else:
        score = None  # ungraded / not submitted — a legitimate state

    level = (row.get("achievement_level") or "").strip().upper()
    if level and level not in ACHIEVEMENT_LEVELS:
        raise GradeError(
            f"'{level}' is not an achievement level. Use one of {', '.join(sorted(ACHIEVEMENT_LEVELS))}."
        )

    return student_id, {
        "score": score,
        "comment": (row.get("comment") or "")[:2000],
        "achievement_level": level,
    }


class RubricError(Exception):
    """A rubric marking action was refused (→ HTTP 400/409)."""


def mark_against_rubric(*, assessment, student_id, selections, comment="", tenant_id):
    """
    Record a level per criterion and derive the student's score from them.

    The score is *computed*, never typed alongside. A rubric where the total
    can disagree with the criteria is worse than no rubric — a student shown a
    breakdown that does not add up to their grade stops trusting either.

    Partial marking is allowed: a teacher gets through the structure criterion
    for the whole class before starting on evidence, and being forced to finish
    one script completely before saving is how work gets lost.
    """
    from decimal import Decimal

    from products.cyed.gradebook.models import Grade, RubricLevel, RubricMark

    rubric = assessment.rubric
    if rubric is None:
        raise RubricError("This assessment has no rubric attached.")
    if not isinstance(selections, dict) or not selections:
        raise RubricError("Give a level for at least one criterion.")

    criteria = {str(c.id): c for c in rubric.criteria.all()}
    levels = {
        str(level.id): level
        for level in RubricLevel.objects.filter(criterion__rubric=rubric)
    }

    chosen = {}
    for criterion_id, level_id in selections.items():
        criterion = criteria.get(str(criterion_id))
        if criterion is None:
            raise RubricError("That criterion does not belong to this assessment's rubric.")
        level = levels.get(str(level_id))
        if level is None or str(level.criterion_id) != str(criterion.id):
            # Catches the copy-paste error that silently scores a student
            # against the wrong criterion's band.
            raise RubricError(
                f"'{level_id}' is not a level on the '{criterion.name}' criterion."
            )
        chosen[criterion] = level

    with transaction.atomic():
        grade, _ = Grade.objects.get_or_create(
            tenant_id=tenant_id, assessment=assessment, student_id=student_id
        )
        for criterion, level in chosen.items():
            RubricMark.objects.update_or_create(
                tenant_id=tenant_id, grade=grade, criterion=criterion,
                defaults={"level": level},
            )

        marks = list(
            RubricMark.objects.filter(tenant_id=tenant_id, grade=grade)
            .select_related("criterion", "level")
        )
        earned = sum((m.weighted_marks() for m in marks), Decimal("0"))
        possible = rubric.total_marks()

        grade.score = earned
        # Scale to the assessment's own maximum when the two differ, so a
        # rubric out of 24 still reports sensibly on a task marked out of 100.
        if possible and assessment.max_score and possible != Decimal(assessment.max_score):
            grade.score = (earned / possible * Decimal(assessment.max_score)).quantize(
                Decimal("0.01")
            )
        if comment:
            grade.comment = comment
        # Carry the achievement level up when every criterion agrees on one —
        # a teacher should not re-judge A–E they have already implicitly given.
        letters = {m.level.achievement_level for m in marks if m.level.achievement_level}
        if len(letters) == 1:
            grade.achievement_level = letters.pop()
        else:
            # The criteria disagree, so no letter is derivable. Any letter still
            # sitting on the grade was typed against a different score and now
            # contradicts it — a 15/16 labelled D is worse than no label.
            # Cleared rather than guessed: the A–E cut-offs are the school's
            # policy, not this function's to invent.
            grade.achievement_level = ""
        grade.save(update_fields=["score", "comment", "achievement_level", "updated_at"])

    return {
        "grade": str(grade.id),
        "student": str(student_id),
        "criteria_marked": len(marks),
        "criteria_total": len(criteria),
        "complete": len(marks) == len(criteria),
        "earned": str(earned),
        "possible": str(possible),
        "score": str(grade.score),
        "achievement_level": grade.achievement_level,
    }


def rubric_breakdown(grade):
    """
    The per-criterion feedback a student reads and a teacher shows a parent.
    """
    marks = grade.rubric_marks.select_related("criterion", "level").all()
    return {
        "grade": str(grade.id),
        "score": str(grade.score) if grade.score is not None else None,
        "achievement_level": grade.achievement_level,
        "criteria": [
            {
                "criterion": m.criterion.name,
                "level": m.level.label,
                "descriptor": m.level.descriptor,
                "marks": str(m.level.marks),
                "weight": str(m.criterion.weight),
                "weighted": str(m.weighted_marks()),
                "comment": m.comment,
            }
            for m in marks
        ],
    }


def bulk_enter_grades(*, assessment, rows, tenant_id):
    """
    Enter or amend a whole assessment's marks in one operation.

    Returns a summary. Re-submitting is an update, not a duplicate: a teacher
    correcting one mark after handing back the papers is routine, and the
    unique (assessment, student) constraint means the alternative would be a
    hard error on a perfectly reasonable action.
    """
    if not isinstance(rows, list) or not rows:
        raise GradeError("'grades' must be a non-empty list.")

    roster = roster_student_ids(assessment.class_section_id, tenant_id)

    cleaned = {}
    for row in rows:
        student_id, values = _clean_row(row, assessment, roster)
        if student_id in cleaned:
            raise GradeError(f"Student {student_id} appears twice in 'grades'.")
        cleaned[student_id] = values

    with transaction.atomic():
        existing = {
            str(g.student_id): g
            for g in Grade.objects.filter(tenant_id=tenant_id, assessment=assessment)
        }
        to_create, to_update = [], []
        for student_id, values in cleaned.items():
            current = existing.get(student_id)
            if current is None:
                to_create.append(Grade(
                    tenant_id=tenant_id, assessment=assessment, student_id=student_id, **values
                ))
            elif any(getattr(current, f) != values[f] for f in GRADE_FIELDS):
                for field, value in values.items():
                    setattr(current, field, value)
                to_update.append(current)

        if to_create:
            Grade.objects.bulk_create(to_create)
        if to_update:
            Grade.objects.bulk_update(to_update, list(GRADE_FIELDS) + ["updated_at"])

    return {
        "assessment": str(assessment.id),
        "submitted": len(cleaned),
        "created": len(to_create),
        "updated": len(to_update),
        "unchanged": len(cleaned) - len(to_create) - len(to_update),
        "ungraded_remaining": max(0, len(roster) - Grade.objects.filter(
            tenant_id=tenant_id, assessment=assessment, score__isnull=False
        ).count()),
    }
