"""
Roll marking.

The audit's finding: marking a class of 30 took 30 HTTP requests, each firing a
`post_save` signal that sent guardian notifications *inside* the write
transaction. Two separate problems live in that sentence.

**Throughput.** A teacher takes the roll in the first two minutes of a lesson,
on a phone or a tablet, often on school wifi. Thirty round trips is not a
performance nitpick — it is the difference between a roll that gets taken and
one that gets skipped. `take_roll` does the whole class in one request.

**Correctness.** Notifying inside the transaction means a request that fails
after the notification has gone out leaves a guardian told their child is
absent when no such mark exists. In-app notifications roll back with the
transaction and hide it, but the moment a real SMS provider is wired that
becomes an unrecallable message about a child's safety. Every notification here
is therefore dispatched from `transaction.on_commit` — after the marks are
durably recorded, or not at all.

Roll marking is *exception-based*, matching how teachers actually work: send
the handful of students who are not present, and everyone else on the roster is
recorded with `default_status`. Sending nothing marks the whole class present.
"""

from django.db import transaction
from django.utils import timezone

from products.cyed.attendance.models import AttendanceMark, RollCall
from products.cyed.sis.models import Enrolment

MARK_FIELDS = ("status", "minutes_late", "note")


class RollError(Exception):
    """The roll was refused for a business reason (→ HTTP 400)."""


def roster_student_ids(class_section_id, tenant_id) -> list:
    """Students actively enrolled in this section, in roll order."""
    return list(
        Enrolment.objects.filter(
            tenant_id=tenant_id, class_section_id=class_section_id, status="active"
        )
        .order_by("student__last_name", "student__first_name")
        .values_list("student_id", flat=True)
    )


def _index_submitted(marks):
    """
    Normalise the submitted exceptions into {student_id: {field: value}}.

    A student sent twice is an error, not a last-one-wins: it means the client
    built the payload wrong, and silently picking one of two conflicting
    statuses for a duty-of-care record is not a choice software should make.
    """
    if marks is None:
        return {}
    if not isinstance(marks, list):
        raise RollError("'marks' must be a list of {student, status} objects.")

    valid = {c[0] for c in AttendanceMark.STATUS_CHOICES}
    indexed = {}
    for row in marks:
        if not isinstance(row, dict):
            raise RollError("Each entry in 'marks' must be an object.")
        student_id = row.get("student")
        if not student_id:
            raise RollError("Each entry in 'marks' needs a 'student'.")
        student_id = str(student_id)
        if student_id in indexed:
            raise RollError(f"Student {student_id} appears twice in 'marks'.")

        status = row.get("status") or "present"
        if status not in valid:
            raise RollError(f"'{status}' is not a valid attendance status.")

        minutes_late = row.get("minutes_late") or 0
        try:
            minutes_late = int(minutes_late)
        except (TypeError, ValueError):
            raise RollError(f"minutes_late for {student_id} must be a whole number of minutes.")
        if minutes_late < 0:
            raise RollError("minutes_late cannot be negative.")

        indexed[student_id] = {
            "status": status,
            "minutes_late": minutes_late,
            "note": (row.get("note") or "")[:255],
        }
    return indexed


def take_roll(
    *, tenant_id, class_section_id, date, period_label="", marks=None,
    default_status="present", taken_by="",
):
    """
    Record attendance for a whole class in one operation.

    Returns (roll_call, summary). Idempotent by design: re-submitting the same
    roll updates the existing marks rather than failing or duplicating, because
    a teacher correcting a mistake five minutes later is the normal case, not
    an exceptional one.

    Only the *newly* absent are notified. A correction from `absent` to `absent`
    must not send a parent a second alert about the same morning.
    """
    valid = {c[0] for c in AttendanceMark.STATUS_CHOICES}
    if default_status not in valid:
        raise RollError(f"'{default_status}' is not a valid attendance status.")

    submitted = _index_submitted(marks)
    roster = roster_student_ids(class_section_id, tenant_id)
    if not roster:
        raise RollError(
            "No students are actively enrolled in this class section, so there is no roll to take."
        )

    # A student who is not on the roster is a client bug or a wrong class — and
    # writing the mark anyway would put a child's attendance record against a
    # lesson they do not attend.
    strays = sorted(set(submitted) - {str(s) for s in roster})
    if strays:
        raise RollError(
            f"{len(strays)} student(s) are not enrolled in this class section: {', '.join(strays)}"
        )

    notify_ids = []
    with transaction.atomic():
        roll_call, _ = RollCall.objects.get_or_create(
            tenant_id=tenant_id, class_section_id=class_section_id,
            date=date, period_label=period_label or "",
            defaults={"taken_by": taken_by or ""},
        )
        if taken_by and roll_call.taken_by != taken_by:
            roll_call.taken_by = taken_by
            roll_call.save(update_fields=["taken_by", "updated_at"])

        existing = {str(m.student_id): m for m in roll_call.marks.all()}
        # Snapshot the pre-write statuses before anything is mutated — the
        # "who newly became absent" question can only be answered against them.
        previous_status = {key: mark.status for key, mark in existing.items()}

        to_create, to_update = [], []
        for student_id in roster:
            key = str(student_id)
            desired = submitted.get(key) or {"status": default_status, "minutes_late": 0, "note": ""}
            current = existing.get(key)

            if current is None:
                to_create.append(AttendanceMark(
                    tenant_id=tenant_id, roll_call=roll_call, student_id=student_id, **desired
                ))
            elif any(getattr(current, f) != desired[f] for f in MARK_FIELDS):
                for field, value in desired.items():
                    setattr(current, field, value)
                to_update.append(current)

        notify_ids = _absence_transitions(
            previous_status, submitted, roster, default_status, to_create
        )

        if to_create:
            AttendanceMark.objects.bulk_create(to_create)
        if to_update:
            AttendanceMark.objects.bulk_update(to_update, list(MARK_FIELDS) + ["updated_at"])

        # A family who told the school in advance must not then be alerted as
        # though they had not. Excuse those marks and drop them from the alerts.
        pre_explained = apply_planned_explanations(tenant_id, roll_call, roster)
        if pre_explained:
            notify_ids = [s for s in notify_ids if s not in pre_explained]

        if notify_ids:
            # Guardians are told only once the marks are durably committed.
            # Deliberately not inside the transaction: see the module docstring.
            roll_call_id = roll_call.id
            transaction.on_commit(
                lambda: notify_absences(tenant_id, roll_call_id, notify_ids)
            )

    summary = {
        "roll_call": str(roll_call.id),
        "roster": len(roster),
        "created": len(to_create),
        "updated": len(to_update),
        "unchanged": len(roster) - len(to_create) - len(to_update),
        "pre_explained": len(pre_explained),
        "notified": len(notify_ids),
        "by_status": _tally(roster, submitted, default_status),
    }
    return roll_call, summary


ABSENCE_STATUSES = {"absent", "late", "left_early"}


def _absence_transitions(previous_status, submitted, roster, default_status, to_create):
    """
    Which students newly moved into an absence state on this submission.

    Read against the pre-write snapshot, so a teacher fixing a typo in an
    absence note does not send the parent a second alert about the same
    morning. `previous_status` maps student id → status before this write;
    a student absent from it had no mark yet.
    """
    moved = []
    created_ids = {str(m.student_id) for m in to_create}
    for student_id in roster:
        key = str(student_id)
        desired = submitted.get(key, {}).get("status", default_status)
        if desired not in ABSENCE_STATUSES:
            continue
        if key in created_ids:
            moved.append(key)
        elif previous_status.get(key) not in ABSENCE_STATUSES:
            moved.append(key)
    return moved


def _tally(roster, submitted, default_status):
    counts = {}
    for student_id in roster:
        status = submitted.get(str(student_id), {}).get("status", default_status)
        counts[status] = counts.get(status, 0) + 1
    return counts


class ExplanationError(Exception):
    """An absence explanation was refused for a business reason (→ HTTP 400/409)."""


def accept_explanation(explanation, *, actor="", note="", as_at=None):
    """
    Accept a family's explanation and excuse the marks it covers.

    Only marks in `EXPLAINABLE` are touched: a day the student was marked
    present has nothing to excuse, and silently rewriting it would corrupt the
    record the department audits.

    A planned explanation legitimately excuses nothing today — the absence has
    not happened yet. That is not a failure, and `apply_planned_explanations`
    picks it up when the roll is taken.
    """
    from products.cyed.attendance.models import AbsenceExplanation, AttendanceMark

    if explanation.status != "submitted":
        raise ExplanationError(f"This explanation has already been {explanation.status}.")

    marks = AttendanceMark.objects.filter(
        tenant_id=explanation.tenant_id,
        student_id=explanation.student_id,
        status__in=AbsenceExplanation.EXPLAINABLE,
        roll_call__date__gte=explanation.start_date,
        roll_call__date__lte=explanation.end_date,
    )
    updated = marks.update(
        status="excused",
        note=f"Explained: {explanation.get_reason_display()}"[:255],
    )

    explanation.status = "accepted"
    explanation.reviewed_by = actor[:255]
    explanation.reviewed_on = timezone.now()
    explanation.review_note = note[:255]
    explanation.marks_updated = updated
    explanation.save(update_fields=[
        "status", "reviewed_by", "reviewed_on", "review_note", "marks_updated", "updated_at",
    ])
    return updated


def decline_explanation(explanation, *, actor="", note=""):
    """
    Decline it. Requires a reason — a family told "no" with no explanation will
    ring the office, which is the call this feature exists to prevent.
    """
    if explanation.status != "submitted":
        raise ExplanationError(f"This explanation has already been {explanation.status}.")
    if not (note or "").strip():
        raise ExplanationError("Give a reason when declining an explanation.")

    explanation.status = "declined"
    explanation.reviewed_by = actor[:255]
    explanation.reviewed_on = timezone.now()
    explanation.review_note = note.strip()[:255]
    explanation.save(update_fields=[
        "status", "reviewed_by", "reviewed_on", "review_note", "updated_at",
    ])
    return explanation


def apply_planned_explanations(tenant_id, roll_call, student_ids):
    """
    Excuse marks already covered by an accepted, forward-dated explanation.

    Called as part of taking the roll. Without this, a parent who told the
    school on Monday about Tuesday's appointment still gets an absence alert on
    Tuesday — which teaches families that telling the school achieves nothing.

    Returns the ids excused, so the caller can leave them out of the alerts.
    """
    from products.cyed.attendance.models import AbsenceExplanation, AttendanceMark

    day = roll_call.date
    covered = set(
        str(s) for s in AbsenceExplanation.objects.filter(
            tenant_id=tenant_id,
            status="accepted",
            student_id__in=student_ids,
            start_date__lte=day,
            end_date__gte=day,
        ).values_list("student_id", flat=True)
    )
    if not covered:
        return set()

    AttendanceMark.objects.filter(
        tenant_id=tenant_id,
        roll_call=roll_call,
        student_id__in=covered,
        status__in=AbsenceExplanation.EXPLAINABLE,
    ).update(status="excused", note="Explained in advance by family")
    return covered


def notify_absences(tenant_id, roll_call_id, student_ids):
    """
    Send guardian alerts for a set of marks, after commit.

    Failures are contained per-student: one guardian with a malformed email
    must not stop the rest of the class's parents being told.
    """
    from products.cyed.notifications.services import notify_guardians_of_absence

    marks = AttendanceMark.objects.select_related("student", "roll_call").filter(
        tenant_id=tenant_id, roll_call_id=roll_call_id, student_id__in=student_ids
    )
    sent = 0
    for mark in marks:
        sent += len(notify_guardians_of_absence(mark))
    return sent
