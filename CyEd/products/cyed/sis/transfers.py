"""
Campus transfers within a school group.

Moving a child between campuses is not a field edit. Their class placements
belong to the campus they are leaving, their bills carry a campus for
per-site reporting, and the history has to survive so an attendance return or
an incident can be attributed to the right site months later.
"""

from django.db import transaction
from django.utils import timezone

from products.cyed.sis.models import CampusTransfer, Enrolment


class TransferError(Exception):
    """A transfer was refused for a business reason (→ HTTP 400/409)."""


@transaction.atomic
def transfer_student(student, *, to_campus, effective_on=None, reason="", requested_by=""):
    """
    Move a student to another campus, ending placements at the old one.

    Class placements are ended rather than moved: a section belongs to a
    campus, so carrying an enrolment across would leave the child on a roll at
    a site they no longer attend — and their new teachers would not see them
    at all. Re-placement at the destination is a separate, deliberate act.
    """
    effective_on = effective_on or timezone.localdate()

    if to_campus is None:
        raise TransferError("A destination campus is required.")
    if str(to_campus.tenant_id) != str(student.tenant_id):
        raise TransferError("That campus belongs to a different school group.")
    if student.campus_id and str(student.campus_id) == str(to_campus.id):
        raise TransferError(f"{student.first_name} is already at {to_campus.name}.")

    from_campus = student.campus

    # End placements that belong to the campus being left. Sections with no
    # campus are group-wide (an online elective) and are left alone.
    ended = Enrolment.objects.filter(
        tenant_id=student.tenant_id, student=student, status="active",
        class_section__campus_id=from_campus.id if from_campus else None,
    ).update(status="completed")

    record = CampusTransfer.objects.create(
        tenant_id=student.tenant_id, student=student,
        from_campus=from_campus, to_campus=to_campus,
        effective_on=effective_on, reason=reason[:255], requested_by=requested_by[:255],
        enrolments_ended=ended,
    )

    student.campus = to_campus
    student.save(update_fields=["campus", "updated_at"])

    # Live bills follow the student so per-campus revenue reporting stays
    # truthful; settled and cancelled bills keep the campus they were raised
    # under, because that is where the money was actually earned.
    from products.cyed.billing.models import StudentBill

    StudentBill.objects.filter(
        tenant_id=student.tenant_id, student=student, status__in=["draft", "active"]
    ).update(campus=to_campus)

    return record


def campus_on(student, day):
    """
    Which campus this student was at on a given date.

    Answers the question a bare FK could not: the latest transfer effective on
    or before `day`, falling back to their current campus for the period
    before any transfer was recorded.
    """
    record = (
        student.campus_transfers.filter(effective_on__lte=day)
        .order_by("-effective_on", "-created_at")
        .first()
    )
    if record is not None:
        return record.to_campus
    # No transfer on or before that date — if any later transfer exists, they
    # were at its origin campus; otherwise they have only ever been where they
    # are now.
    earliest = student.campus_transfers.order_by("effective_on", "created_at").first()
    if earliest is not None:
        return earliest.from_campus
    return student.campus
