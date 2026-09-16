"""
Assessment engine: submission lifecycle, auto-marking, and gradebook write-back.

Pure-ish functions over model instances so every rule is unit-testable without
going through HTTP. The views translate the exceptions raised here into 400s.
"""

from decimal import ROUND_HALF_UP, Decimal

from django.db.models import Max
from django.utils import timezone

from products.cyed.assessment.models import (
    AUTO_GRADED_KINDS,
    CHOICE_KINDS,
    KIND_ESSAY,
    KIND_MULTI_SELECT,
    KIND_SHORT_ANSWER,
    Answer,
    QuizAttempt,
    Submission,
)

CENTS = Decimal("0.01")


# ── Errors (views map these to HTTP 400) ─────────────────────────────────────
class AssessmentRefused(Exception):
    """Base for a rule the caller broke."""


class LateSubmissionRefused(AssessmentRefused):
    pass


class AttemptLimitReached(AssessmentRefused):
    pass


class AlreadySubmitted(AssessmentRefused):
    pass


# ── Helpers ──────────────────────────────────────────────────────────────────
def normalise_text(value) -> str:
    """Case-insensitive, whitespace-trimmed form used for short-answer matching."""
    return " ".join(str(value or "").strip().lower().split())


def _money(value: Decimal) -> Decimal:
    return Decimal(value).quantize(CENTS, rounding=ROUND_HALF_UP)


def achievement_level_for(percentage) -> str:
    """A–E against the Australian Curriculum achievement standard."""
    if percentage is None:
        return ""
    if percentage >= 85:
        return "A"
    if percentage >= 70:
        return "B"
    if percentage >= 50:
        return "C"
    if percentage >= 25:
        return "D"
    return "E"


# ── Assignment submissions ───────────────────────────────────────────────────
def submit_submission(submission: Submission, when=None) -> Submission:
    """
    Hand a submission in.

    Past the deadline with allow_late=False this is REFUSED outright; with
    allow_late=True it is accepted and flagged `late`.
    """
    when = when or timezone.now()
    assignment = submission.assignment
    overdue = bool(assignment.due_at and when > assignment.due_at)
    if overdue and not assignment.allow_late:
        raise LateSubmissionRefused(
            "The due date for this assignment has passed and late submissions are not accepted."
        )
    submission.status = Submission.LATE if overdue else Submission.SUBMITTED
    submission.submitted_at = when
    submission.save(update_fields=["status", "submitted_at", "updated_at"])
    return submission


def sync_gradebook_grade(submission: Submission):
    """
    Push a marked submission into the gradebook.

    This is the whole point of Assignment.assessment: the student-facing
    submission is the source, `cyed_gradebook.Grade` is the mark of record.
    Returns the Grade, or None when the assignment is not linked / not marked.
    """
    assignment = submission.assignment
    if not assignment.assessment_id or submission.score is None:
        return None

    from products.cyed.gradebook.models import Grade

    percentage = submission.percentage
    grade, _created = Grade.objects.update_or_create(
        tenant_id=submission.tenant_id,
        assessment_id=assignment.assessment_id,
        student_id=submission.student_id,
        defaults={
            "score": submission.score,
            "comment": submission.feedback,
            "achievement_level": achievement_level_for(percentage),
        },
    )
    return grade


def grade_submission(submission: Submission, score, feedback: str = "", marker: str = ""):
    """Teacher marks a submission; the gradebook row follows automatically."""
    submission.score = _money(Decimal(str(score)))
    submission.feedback = feedback or ""
    submission.graded_by = marker or ""
    submission.graded_at = timezone.now()
    submission.status = Submission.GRADED
    submission.save(
        update_fields=["score", "feedback", "graded_by", "graded_at", "status", "updated_at"]
    )
    return submission, sync_gradebook_grade(submission)


# ── Quiz attempts ────────────────────────────────────────────────────────────
def start_attempt(quiz, student, tenant_id, when=None) -> QuizAttempt:
    """Open a new attempt, enforcing Quiz.max_attempts."""
    existing = QuizAttempt.objects.filter(tenant_id=tenant_id, quiz=quiz, student=student)
    used = existing.count()
    if quiz.max_attempts and used >= quiz.max_attempts:
        raise AttemptLimitReached(
            f"You have used all {quiz.max_attempts} permitted attempt(s) for this quiz."
        )
    highest = existing.aggregate(m=Max("attempt_number"))["m"] or 0
    return QuizAttempt.objects.create(
        tenant_id=tenant_id,
        quiz=quiz,
        student=student,
        attempt_number=highest + 1,
        started_at=when or timezone.now(),
        max_score=quiz.total_points,
    )


def save_answer(attempt: QuizAttempt, question, selected_choice_ids=None, text_answer: str = ""):
    """
    Record (or replace) the student's response to one question. Marking does not
    happen here — nothing is revealed until the attempt is submitted.
    """
    answer, _ = Answer.objects.get_or_create(
        tenant_id=attempt.tenant_id, attempt=attempt, question=question
    )
    answer.text_answer = text_answer or ""
    answer.awarded_points = None
    answer.is_correct = None
    answer.save(update_fields=["text_answer", "awarded_points", "is_correct", "updated_at"])
    if question.kind in CHOICE_KINDS:
        valid = list(question.choices.filter(id__in=list(selected_choice_ids or [])))
        answer.selected_choices.set(valid)
    else:
        answer.selected_choices.clear()
    return answer


def grade_answer(answer: Answer):
    """
    Auto-mark one answer. Returns the awarded Decimal, or None for an essay
    (which is left for a human and keeps awarded_points untouched).
    """
    question = answer.question
    points = Decimal(question.points)

    if question.kind == KIND_ESSAY:
        return None

    if question.kind in CHOICE_KINDS:
        correct = set(question.choices.filter(is_correct=True).values_list("id", flat=True))
        selected = set(answer.selected_choices.values_list("id", flat=True))
        if not correct:
            # Misconfigured question — never punish the student for it.
            awarded, is_correct = Decimal("0"), False
        elif question.kind == KIND_MULTI_SELECT:
            hits = len(selected & correct)
            wrong = len(selected - correct)
            # Proportional partial credit, penalising wrong ticks but never
            # dropping below zero.
            ratio = (Decimal(hits) - Decimal(wrong)) / Decimal(len(correct))
            if ratio < 0:
                ratio = Decimal("0")
            awarded = _money(points * ratio)
            is_correct = selected == correct
        else:  # multiple_choice / true_false — all-or-nothing
            is_correct = selected == correct
            awarded = points if is_correct else Decimal("0")
    elif question.kind == KIND_SHORT_ANSWER:
        accepted = {normalise_text(a) for a in (question.accepted_answers or []) if str(a).strip()}
        is_correct = bool(accepted) and normalise_text(answer.text_answer) in accepted
        awarded = points if is_correct else Decimal("0")
    else:  # pragma: no cover - defensive: unknown kind is never auto-marked
        return None

    answer.awarded_points = _money(awarded)
    answer.is_correct = is_correct
    answer.save(update_fields=["awarded_points", "is_correct", "updated_at"])
    return answer.awarded_points


def mark_answer(answer: Answer, awarded_points, is_correct=None) -> Answer:
    """Human marking of an essay (or an override of an auto-marked answer)."""
    points = _money(Decimal(str(awarded_points)))
    if points < 0:
        points = Decimal("0.00")
    if points > Decimal(answer.question.points):
        points = _money(Decimal(answer.question.points))
    answer.awarded_points = points
    if is_correct is None:
        is_correct = points >= Decimal(answer.question.points)
    answer.is_correct = bool(is_correct)
    answer.save(update_fields=["awarded_points", "is_correct", "updated_at"])
    return answer


def grade_attempt(attempt: QuizAttempt, reveal_key: bool = False) -> dict:
    """
    Auto-mark every auto-gradable answer on the attempt and roll up the score.

    `is_graded` only becomes True once nothing is left for a human — i.e. every
    essay has been marked. Returns a per-question breakdown; `reveal_key` adds
    the correct choice ids and is only ever passed for a submitted attempt.
    """
    questions = list(attempt.quiz.questions.prefetch_related("choices").all())
    answers = {a.question_id: a for a in attempt.answers.select_related("question").all()}

    total = Decimal("0")
    max_total = Decimal("0")
    pending = False
    breakdown = []

    for question in questions:
        max_total += Decimal(question.points)
        answer = answers.get(question.id)
        auto = question.kind in AUTO_GRADED_KINDS
        row = {
            "question": str(question.id),
            "sequence": question.sequence,
            "kind": question.kind,
            "points": str(_money(Decimal(question.points))),
            "auto_graded": auto,
            "answered": answer is not None,
        }

        if question.kind == KIND_ESSAY:
            if answer is not None and answer.awarded_points is not None:
                total += answer.awarded_points
                row.update(
                    {
                        "awarded": str(answer.awarded_points),
                        "is_correct": answer.is_correct,
                        "requires_manual_marking": False,
                    }
                )
            else:
                pending = True
                row.update(
                    {"awarded": None, "is_correct": None, "requires_manual_marking": True}
                )
            if answer is not None:
                row["answer"] = str(answer.id)
            breakdown.append(row)
            continue

        if answer is None:
            # Unanswered auto-gradable question scores zero.
            row.update({"awarded": "0.00", "is_correct": False, "requires_manual_marking": False})
        else:
            awarded = grade_answer(answer)
            total += awarded or Decimal("0")
            row.update(
                {
                    "answer": str(answer.id),
                    "awarded": str(answer.awarded_points),
                    "is_correct": answer.is_correct,
                    "requires_manual_marking": False,
                }
            )
        if reveal_key:
            if question.kind in CHOICE_KINDS:
                row["correct_choices"] = [
                    str(c.id) for c in question.choices.all() if c.is_correct
                ]
            elif question.kind == KIND_SHORT_ANSWER:
                row["accepted_answers"] = list(question.accepted_answers or [])
        breakdown.append(row)

    attempt.score = _money(total)
    attempt.max_score = _money(max_total)
    attempt.is_graded = not pending
    attempt.save(update_fields=["score", "max_score", "is_graded", "updated_at"])

    return {
        "attempt": str(attempt.id),
        "student": str(attempt.student_id),
        "attempt_number": attempt.attempt_number,
        "score": str(attempt.score),
        "max_score": str(attempt.max_score),
        "percentage": attempt.percentage,
        "is_graded": attempt.is_graded,
        "awaiting_manual_marking": pending,
        "questions": breakdown,
    }


def submit_attempt(attempt: QuizAttempt, answers_payload=None, when=None) -> dict:
    """
    Hand a quiz in: persist the posted answers, then auto-mark.

    If the time limit has already elapsed the attempt is still accepted and
    marked on whatever was saved before expiry — the newly posted answers are
    ignored rather than the student losing the whole attempt.
    """
    if attempt.submitted_at is not None:
        raise AlreadySubmitted("This attempt has already been submitted.")

    expired = attempt.is_expired
    if not expired:
        by_id = {str(q.id): q for q in attempt.quiz.questions.all()}
        for row in answers_payload or []:
            question = by_id.get(str(row.get("question")))
            if question is None:
                continue
            save_answer(
                attempt,
                question,
                selected_choice_ids=row.get("choices") or row.get("selected_choices") or [],
                text_answer=row.get("text_answer", ""),
            )

    attempt.submitted_at = when or timezone.now()
    attempt.save(update_fields=["submitted_at", "updated_at"])
    result = grade_attempt(attempt, reveal_key=True)
    result["expired"] = expired
    return result
