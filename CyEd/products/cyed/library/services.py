"""
Library circulation rules: borrower limits, due dates, fines, overdue reports.

`overdue` existed as a status with nothing behind it — no fine calculation, no
overdue report, no borrower limit. So the library could mark a book late and
then do nothing about it, and a student could borrow the entire shelf.

The fine rules are deliberately gentle-by-default. A library that blocks a
child from borrowing over twenty cents has stopped being a library, so the
blocking behaviour is opt-in and threshold-based, and fines are capped so a
lost book cannot become a debt larger than the book.
"""

from decimal import Decimal

from django.utils import timezone

from products.cyed.library.models import Loan, get_policy


class CirculationError(Exception):
    """A loan action was refused for a business reason (→ HTTP 400/409)."""


def open_loans(tenant_id, student_id):
    return Loan.objects.filter(
        tenant_id=tenant_id, student_id=student_id, status__in=["borrowed", "overdue"]
    )


def student_fines(tenant_id, student_id, *, as_at=None):
    """Total unpaid, unwaived fines for one borrower."""
    policy = get_policy(tenant_id)
    total = Decimal("0")
    for loan in Loan.objects.filter(tenant_id=tenant_id, student_id=student_id):
        total += loan.outstanding_fine(policy, as_at)
    return total


def check_can_borrow(tenant_id, student, *, as_at=None):
    """
    (allowed, reason). Enforces the borrower limit, and the fine block only if
    the school has turned it on.
    """
    policy = get_policy(tenant_id)
    current = open_loans(tenant_id, student.id).count()
    if policy.max_loans_per_student and current >= policy.max_loans_per_student:
        return False, (
            f"{student.first_name} already has {current} book(s) on loan; the limit is "
            f"{policy.max_loans_per_student}. Return one first."
        )

    if policy.block_borrowing_when_fined:
        owing = student_fines(tenant_id, student.id, as_at=as_at)
        if owing >= Decimal(policy.fine_block_threshold):
            return False, (
                f"{student.first_name} owes {owing} in library fines, at or above the "
                f"{policy.fine_block_threshold} threshold."
            )
    return True, ""


def due_date_for(tenant_id, borrowed_on=None):
    from datetime import timedelta

    policy = get_policy(tenant_id)
    start = borrowed_on or timezone.localdate()
    return start + timedelta(days=policy.loan_days)


def return_loan(loan, *, as_at=None):
    """
    Take a book back and freeze whatever fine it accrued.

    The fine is stamped onto the loan at this moment so a later policy change
    cannot rewrite a figure a family has already been told.
    """
    if loan.status == "returned":
        raise CirculationError("This book has already been returned.")

    as_at = as_at or timezone.localdate()
    policy = get_policy(loan.tenant_id)

    # Order matters: `accrued_fine` short-circuits to the stored `fine_amount`
    # once the loan reads as returned, so flipping the status first would
    # freeze the fine at zero and every late return would be free.
    loan.returned_on = as_at
    loan.fine_amount = loan.accrued_fine(policy, as_at)
    loan.status = "returned"
    loan.save(update_fields=["status", "returned_on", "fine_amount", "updated_at"])

    loan.book.copies_available += 1
    loan.book.save(update_fields=["copies_available", "updated_at"])
    return loan


def renew_loan(loan, *, as_at=None, max_renewals=2):
    """
    Extend a loan. Refused once overdue: a renewal is not a way to make an
    existing fine disappear.
    """
    if loan.status == "returned":
        raise CirculationError("This book has already been returned.")
    as_at = as_at or timezone.localdate()
    if loan.due_on and loan.due_on < as_at:
        raise CirculationError(
            "This loan is already overdue and cannot be renewed. Return the book first."
        )
    if loan.renewed_count >= max_renewals:
        raise CirculationError(
            f"This loan has already been renewed {loan.renewed_count} time(s). "
            f"Return the book so someone else can borrow it."
        )
    loan.due_on = due_date_for(loan.tenant_id, as_at)
    loan.renewed_count += 1
    loan.save(update_fields=["due_on", "renewed_count", "updated_at"])
    return loan


def waive_fine(loan, *, reason, actor=""):
    """Forgive a fine. Requires a reason — a silent waiver is unauditable."""
    if not (reason or "").strip():
        raise CirculationError("Give a reason for waiving the fine.")
    loan.fine_waived = True
    loan.fine_waived_by = actor[:255]
    loan.fine_waive_reason = reason.strip()[:255]
    loan.save(update_fields=[
        "fine_waived", "fine_waived_by", "fine_waive_reason", "updated_at",
    ])
    return loan


def mark_overdue(tenant_id, *, as_at=None):
    """Flip borrowed loans past their due date. Run daily."""
    as_at = as_at or timezone.localdate()
    return Loan.objects.filter(
        tenant_id=tenant_id, status="borrowed", due_on__lt=as_at
    ).update(status="overdue")


def overdue_report(tenant_id, *, as_at=None):
    """
    Every outstanding overdue loan with its running fine — the report the
    librarian actually needs, which did not exist.
    """
    as_at = as_at or timezone.localdate()
    policy = get_policy(tenant_id)
    rows = []
    for loan in Loan.objects.select_related("book", "student").filter(
        tenant_id=tenant_id, status__in=["borrowed", "overdue"], due_on__lt=as_at
    ):
        rows.append({
            "loan": str(loan.id),
            "student": str(loan.student_id),
            "student_name": f"{loan.student.first_name} {loan.student.last_name}".strip(),
            "year_level": loan.student.year_level,
            "book": loan.book.title,
            "due_on": loan.due_on.isoformat() if loan.due_on else None,
            "days_overdue": loan.days_overdue(as_at),
            "fine": str(loan.outstanding_fine(policy, as_at)),
        })
    rows.sort(key=lambda r: r["days_overdue"], reverse=True)
    return {
        "as_at": as_at.isoformat(),
        "count": len(rows),
        "total_fines": str(sum((Decimal(r["fine"]) for r in rows), Decimal("0"))),
        "results": rows,
    }
