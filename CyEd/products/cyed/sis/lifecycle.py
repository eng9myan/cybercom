"""
The end of a student's time at the school: exit, Transfer Certificate, alumni.

Enrolment was well covered; leaving was not. A student could be flipped to
`withdrawn` and that was the whole of it — no exit workflow, no Transfer
Certificate, no final-fee settlement, and no distinction between a child who
graduated and one who left in Year 8.

A Transfer Certificate matters because the receiving school needs it: it states
what the child completed, that their fees were settled, and that they left in
good standing. Issuing one before the account is clear, or before the exit
checks are done, is how a school ends up certifying something it cannot support.
"""

from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from products.cyed.sis.models import Enrolment, Student, TransferCertificate


class LifecycleError(Exception):
    """An exit action was refused for a business reason (→ HTTP 400/409)."""


def exit_checks(student) -> dict:
    """
    What still stands between this student and a clean exit.

    Returns each check with a verdict rather than one boolean, because the
    registrar needs to know *which* thing to chase, and because some of these
    are waivable by leadership and others are not.
    """
    checks = []

    outstanding = _outstanding_fees(student)
    checks.append({
        "check": "fees",
        "passed": outstanding <= 0,
        "detail": (
            "Account settled." if outstanding <= 0
            else f"{outstanding} outstanding across bills and invoices."
        ),
        "waivable": True,
    })

    open_loans = student.loans.filter(status__in=["borrowed", "overdue"]).count()
    checks.append({
        "check": "library",
        "passed": open_loans == 0,
        "detail": "No books on loan." if open_loans == 0 else f"{open_loans} book(s) not returned.",
        "waivable": True,
    })

    active_classes = Enrolment.objects.filter(
        tenant_id=student.tenant_id, student=student, status="active"
    ).count()
    checks.append({
        "check": "class_enrolments",
        "passed": True,  # informational: exiting closes these automatically
        "detail": (
            f"{active_classes} active class enrolment(s) will be closed."
            if active_classes else "No active class enrolments."
        ),
        "waivable": True,
    })

    return {
        "student": str(student.id),
        "name": f"{student.first_name} {student.last_name}".strip(),
        "clear": all(c["passed"] for c in checks),
        "checks": checks,
    }


def _outstanding_fees(student) -> Decimal:
    from products.cyed.billing.models import StudentBill
    from products.cyed.fees.models import Invoice

    total = Decimal("0")
    for bill in StudentBill.objects.filter(
        tenant_id=student.tenant_id, student=student
    ).exclude(status="cancelled"):
        total += bill.balance
    for invoice in Invoice.objects.filter(
        tenant_id=student.tenant_id, student=student
    ).exclude(status="cancelled"):
        total += invoice.balance
    return total


@transaction.atomic
def exit_student(student, *, reason, exit_date=None, destination="", actor="",
                 graduated=False, override_reason=""):
    """
    Close a student's enrolment properly.

    Ends their class enrolments, cancels transport, closes any dunning case,
    and marks them `graduated` or `withdrawn` — the distinction matters, and a
    system that records every leaver identically cannot produce an alumni list.

    Outstanding fees or library books block the exit unless leadership
    overrides with a reason: letting a student walk out silently is how a debt
    becomes unrecoverable, but refusing outright would trap families who are
    genuinely moving on.
    """
    if student.enrolment_status in ("graduated", "withdrawn"):
        raise LifecycleError(f"This student has already left ({student.enrolment_status}).")

    exit_date = exit_date or timezone.localdate()
    checks = exit_checks(student)
    if not checks["clear"] and not override_reason:
        blocking = [c["check"] for c in checks["checks"] if not c["passed"]]
        raise LifecycleError(
            f"Exit blocked by: {', '.join(blocking)}. Resolve them, or supply an "
            f"'override_reason' to exit anyway."
        )

    Enrolment.objects.filter(
        tenant_id=student.tenant_id, student=student, status="active"
    ).update(status="completed")

    from products.cyed.transport.models import TransportSubscription

    TransportSubscription.objects.filter(
        tenant_id=student.tenant_id, student=student, status="active"
    ).update(status="cancelled")

    student.enrolment_status = "graduated" if graduated else "withdrawn"
    student.exit_date = exit_date
    student.exit_reason = (reason or "")[:255]
    student.exit_destination = destination[:255]
    student.save(update_fields=[
        "enrolment_status", "exit_date", "exit_reason", "exit_destination", "updated_at",
    ])

    # A family whose last child has left should stop receiving fee letters.
    _close_dunning_if_no_children_left(student)
    return student


def _close_dunning_if_no_children_left(student):
    from products.cyed.billing.collections import resolve
    from products.cyed.billing.models import DunningCase

    family = student.family
    if family is None or family.students_enrolled().exists():
        return
    for case in DunningCase.objects.filter(
        tenant_id=student.tenant_id, family=family, status__in=["open", "paused"]
    ):
        resolve(case, note="All children have left the school; case closed for review.")


@transaction.atomic
def issue_transfer_certificate(student, *, actor="", notes="", override_reason=""):
    """
    Issue the certificate the receiving school asks for.

    Refuses while the account is unsettled unless overridden, because the
    certificate asserts good standing — certifying it over an unpaid balance
    is a statement the school cannot support.
    """
    if student.enrolment_status not in ("graduated", "withdrawn"):
        raise LifecycleError(
            "Exit the student before issuing a Transfer Certificate — the certificate "
            "states when and why they left."
        )

    checks = exit_checks(student)
    if not checks["clear"] and not override_reason:
        blocking = [c["check"] for c in checks["checks"] if not c["passed"]]
        raise LifecycleError(
            f"A Transfer Certificate asserts the student left in good standing, but "
            f"these are outstanding: {', '.join(blocking)}."
        )

    existing = TransferCertificate.objects.filter(
        tenant_id=student.tenant_id, student=student
    ).order_by("-version").first()
    version = (existing.version if existing else 0) + 1

    return TransferCertificate.objects.create(
        tenant_id=student.tenant_id,
        student=student,
        version=version,
        number=f"TC-{timezone.localdate():%Y}-{str(student.id)[:8]}-{version}",
        issued_on=timezone.localdate(),
        issued_by=actor[:255],
        snapshot=_certificate_snapshot(student, checks),
        notes=notes[:500],
        fees_settled=checks["checks"][0]["passed"],
    )


def _certificate_snapshot(student, checks) -> dict:
    """
    Frozen facts at the moment of issue.

    Stored rather than rendered on demand: a certificate reissued next year
    must still say what it said, even if the student record has since changed.
    """
    last_year = (
        Enrolment.objects.filter(tenant_id=student.tenant_id, student=student)
        .select_related("class_section__academic_year")
        .order_by("-created_at").first()
    )
    return {
        "student": {
            "name": f"{student.first_name} {student.last_name}".strip(),
            "student_number": student.student_number,
            "date_of_birth": student.date_of_birth.isoformat() if student.date_of_birth else None,
            "year_level_at_exit": student.year_level,
            "usi": student.usi,
            "state_student_number": student.state_student_number,
        },
        "enrolment": {
            "status": student.enrolment_status,
            "exit_date": student.exit_date.isoformat() if student.exit_date else None,
            "exit_reason": student.exit_reason,
            "destination": student.exit_destination,
            "last_class": (
                last_year.class_section.name if last_year and last_year.class_section_id else ""
            ),
        },
        "standing": {
            "fees_settled": checks["checks"][0]["passed"],
            "library_clear": checks["checks"][1]["passed"],
        },
        "issued_at": timezone.now().isoformat(),
    }


def alumni(tenant_id, *, year=None, year_level=None):
    """
    Former students, most recent leavers first.

    Graduates and withdrawals both appear — a school's alumni relations care
    about everyone who passed through — but the status is carried so the two
    can be told apart.
    """
    qs = Student.objects.filter(
        tenant_id=tenant_id, enrolment_status__in=["graduated", "withdrawn"]
    )
    if year:
        qs = qs.filter(exit_date__year=year)
    if year_level:
        qs = qs.filter(year_level=year_level)

    return [
        {
            "student": str(s.id),
            "name": f"{s.first_name} {s.last_name}".strip(),
            "status": s.enrolment_status,
            "year_level_at_exit": s.year_level,
            "exit_date": s.exit_date.isoformat() if s.exit_date else None,
            "exit_reason": s.exit_reason,
            "destination": s.exit_destination,
            "email": s.email,
        }
        for s in qs.order_by("-exit_date", "last_name")
    ]
