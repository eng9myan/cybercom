"""
Library circulation: borrower limits, fines, overdue reporting.

`overdue` was a status with nothing behind it. These tests cover what was
added, and in particular the deliberate gentleness: a library that blocks a
child over twenty cents has stopped being a library.
"""

import uuid
from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from products.cyed.library import services
from products.cyed.library.models import Book, LibraryPolicy, Loan, get_policy
from products.cyed.sis.models import Student

TODAY = timezone.localdate()


@pytest.fixture
def client_for(mint_token, mock_jwks, tenant_id):
    def _make(roles, email="librarian@cyed.edu.au"):
        c = APIClient()
        c.credentials(HTTP_AUTHORIZATION=f"Bearer {mint_token({
            'sub': str(uuid.uuid4()), 'email': email, 'tenant_id': str(tenant_id),
            'realm_access': {'roles': roles},
        })}")
        return c
    return _make


@pytest.fixture
def librarian(client_for):
    return client_for(["tenant_admin"])


@pytest.fixture
def student(tenant_id):
    return Student.objects.create(
        tenant_id=tenant_id, first_name="Mia", last_name="Tran",
        year_level=8, enrolment_status="enrolled",
    )


@pytest.fixture
def books(tenant_id):
    return [
        Book.objects.create(
            tenant_id=tenant_id, title=f"Book {i}", copies_total=2, copies_available=2
        )
        for i in range(5)
    ]


def _borrow(client, book, student):
    return client.post("/api/v1/library/loans/", {
        "book": str(book.id), "student": str(student.id),
    }, format="json")


# ── borrower limits ──────────────────────────────────────────────────────────
@pytest.mark.django_db
def test_due_date_comes_from_policy_not_the_client(librarian, tenant_id, books, student):
    """A borrower cannot set their own due date by posting one."""
    resp = librarian.post("/api/v1/library/loans/", {
        "book": str(books[0].id), "student": str(student.id),
        "due_on": (TODAY + timedelta(days=365)).isoformat(),
    }, format="json")
    assert resp.status_code == 201, resp.data
    loan = Loan.objects.get(id=resp.data["id"])
    assert loan.due_on == TODAY + timedelta(days=get_policy(tenant_id).loan_days)


@pytest.mark.django_db
def test_borrowing_stops_at_the_limit(librarian, tenant_id, books, student):
    policy = get_policy(tenant_id)
    for i in range(policy.max_loans_per_student):
        assert _borrow(librarian, books[i], student).status_code == 201

    over = _borrow(librarian, books[policy.max_loans_per_student], student)
    assert over.status_code == 400
    assert "the limit is" in str(over.data)


@pytest.mark.django_db
def test_returning_a_book_frees_the_slot(librarian, tenant_id, books, student):
    policy = get_policy(tenant_id)
    loans = []
    for i in range(policy.max_loans_per_student):
        loans.append(_borrow(librarian, books[i], student).data["id"])

    librarian.post(f"/api/v1/library/loans/{loans[0]}/return_book/", {}, format="json")
    assert _borrow(librarian, books[policy.max_loans_per_student], student).status_code == 201


@pytest.mark.django_db
def test_a_book_with_no_copies_cannot_be_borrowed(librarian, tenant_id, student):
    book = Book.objects.create(
        tenant_id=tenant_id, title="Sole copy", copies_total=1, copies_available=0
    )
    assert _borrow(librarian, book, student).status_code == 400


# ── fines ────────────────────────────────────────────────────────────────────
@pytest.mark.django_db
def test_no_fine_inside_the_grace_period(tenant_id, books, student):
    """A weekend or a sick day must not become a debt."""
    policy = get_policy(tenant_id)
    loan = Loan.objects.create(
        tenant_id=tenant_id, book=books[0], student=student,
        due_on=TODAY - timedelta(days=policy.grace_days),
    )
    assert loan.accrued_fine(policy, TODAY) == Decimal("0")


@pytest.mark.django_db
def test_fines_accrue_per_day_after_grace(tenant_id, books, student):
    policy = get_policy(tenant_id)
    loan = Loan.objects.create(
        tenant_id=tenant_id, book=books[0], student=student,
        due_on=TODAY - timedelta(days=policy.grace_days + 5),
    )
    assert loan.accrued_fine(policy, TODAY) == Decimal(policy.fine_per_day) * 5


@pytest.mark.django_db
def test_a_fine_is_capped(tenant_id, books, student):
    """A lost book must not become a debt larger than the book."""
    policy = get_policy(tenant_id)
    loan = Loan.objects.create(
        tenant_id=tenant_id, book=books[0], student=student,
        due_on=TODAY - timedelta(days=5000),
    )
    assert loan.accrued_fine(policy, TODAY) == Decimal(policy.max_fine_per_loan)


@pytest.mark.django_db
def test_returning_freezes_the_fine(librarian, tenant_id, books, student):
    """
    A returned book's fine stops growing — that is the difference between a
    fine and a punishment. It is also frozen against later policy changes.
    """
    policy = get_policy(tenant_id)
    loan = Loan.objects.create(
        tenant_id=tenant_id, book=books[0], student=student, status="overdue",
        due_on=TODAY - timedelta(days=policy.grace_days + 4),
    )
    librarian.post(f"/api/v1/library/loans/{loan.id}/return_book/", {}, format="json")
    loan.refresh_from_db()
    frozen = loan.fine_amount
    assert frozen == Decimal(policy.fine_per_day) * 4

    LibraryPolicy.objects.filter(tenant_id=tenant_id).update(fine_per_day=Decimal("5.00"))
    loan.refresh_from_db()
    assert loan.accrued_fine(get_policy(tenant_id), TODAY) == frozen


@pytest.mark.django_db
def test_waiving_a_fine_requires_a_reason(librarian, tenant_id, books, student):
    loan = Loan.objects.create(
        tenant_id=tenant_id, book=books[0], student=student,
        due_on=TODAY - timedelta(days=30), status="overdue",
    )
    bare = librarian.post(f"/api/v1/library/loans/{loan.id}/waive-fine/", {}, format="json")
    assert bare.status_code == 400

    resp = librarian.post(f"/api/v1/library/loans/{loan.id}/waive-fine/", {
        "reason": "Book was returned to the wrong campus",
    }, format="json")
    assert resp.status_code == 200
    loan.refresh_from_db()
    assert loan.fine_waived and loan.fine_waived_by == "librarian@cyed.edu.au"
    assert loan.outstanding_fine(get_policy(tenant_id)) == Decimal("0")


@pytest.mark.django_db
def test_a_fine_cannot_simply_be_patched_away(librarian, tenant_id, books, student):
    loan = Loan.objects.create(
        tenant_id=tenant_id, book=books[0], student=student,
        due_on=TODAY - timedelta(days=30), status="overdue", fine_amount=Decimal("5.00"),
    )
    librarian.patch(
        f"/api/v1/library/loans/{loan.id}/", {"fine_amount": "0.00"}, format="json"
    )
    loan.refresh_from_db()
    assert loan.fine_amount == Decimal("5.00")


# ── blocking is opt-in ───────────────────────────────────────────────────────
@pytest.mark.django_db
def test_fines_do_not_block_borrowing_by_default(librarian, tenant_id, books, student):
    """A library that locks children out over small debts is not a library."""
    Loan.objects.create(
        tenant_id=tenant_id, book=books[4], student=student, status="returned",
        due_on=TODAY - timedelta(days=100), returned_on=TODAY, fine_amount=Decimal("15.00"),
    )
    assert _borrow(librarian, books[0], student).status_code == 201


@pytest.mark.django_db
def test_a_school_can_turn_blocking_on(librarian, tenant_id, books, student):
    # Materialise the policy row before updating it — `get_policy` creates on
    # first read, so an update against a not-yet-existing row silently does
    # nothing and the test would pass for the wrong reason.
    get_policy(tenant_id)
    LibraryPolicy.objects.filter(tenant_id=tenant_id).update(
        block_borrowing_when_fined=True, fine_block_threshold=Decimal("10.00")
    )
    Loan.objects.create(
        tenant_id=tenant_id, book=books[4], student=student, status="returned",
        due_on=TODAY - timedelta(days=100), returned_on=TODAY, fine_amount=Decimal("15.00"),
    )
    resp = _borrow(librarian, books[0], student)
    assert resp.status_code == 400
    assert "library fines" in str(resp.data)


# ── renewals ─────────────────────────────────────────────────────────────────
@pytest.mark.django_db
def test_renewing_extends_the_due_date(librarian, tenant_id, books, student):
    loan = Loan.objects.create(
        tenant_id=tenant_id, book=books[0], student=student, due_on=TODAY + timedelta(days=2)
    )
    resp = librarian.post(f"/api/v1/library/loans/{loan.id}/renew/", {}, format="json")
    assert resp.status_code == 200
    loan.refresh_from_db()
    assert loan.due_on == services.due_date_for(tenant_id)
    assert loan.renewed_count == 1


@pytest.mark.django_db
def test_an_overdue_loan_cannot_be_renewed(librarian, tenant_id, books, student):
    """Renewal is not a way to make an existing fine disappear."""
    loan = Loan.objects.create(
        tenant_id=tenant_id, book=books[0], student=student,
        due_on=TODAY - timedelta(days=3), status="overdue",
    )
    resp = librarian.post(f"/api/v1/library/loans/{loan.id}/renew/", {}, format="json")
    assert resp.status_code == 409
    assert "already overdue" in resp.data["detail"]


@pytest.mark.django_db
def test_renewals_run_out(librarian, tenant_id, books, student):
    loan = Loan.objects.create(
        tenant_id=tenant_id, book=books[0], student=student,
        due_on=TODAY + timedelta(days=2), renewed_count=2,
    )
    resp = librarian.post(f"/api/v1/library/loans/{loan.id}/renew/", {}, format="json")
    assert resp.status_code == 409


# ── the report that did not exist ────────────────────────────────────────────
@pytest.mark.django_db
def test_overdue_report_lists_longest_overdue_first(librarian, tenant_id, books, student):
    for days in (3, 40, 15):
        Loan.objects.create(
            tenant_id=tenant_id, book=books[0], student=student,
            due_on=TODAY - timedelta(days=days), status="borrowed",
        )
    resp = librarian.get("/api/v1/library/loans/overdue/")
    assert resp.status_code == 200
    assert resp.data["count"] == 3
    assert [r["days_overdue"] for r in resp.data["results"]] == [40, 15, 3]
    assert Decimal(resp.data["total_fines"]) > 0


@pytest.mark.django_db
def test_mark_overdue_sweep_flips_late_loans(librarian, tenant_id, books, student):
    Loan.objects.create(
        tenant_id=tenant_id, book=books[0], student=student,
        due_on=TODAY - timedelta(days=1), status="borrowed",
    )
    resp = librarian.post("/api/v1/library/loans/mark-overdue/", {}, format="json")
    assert resp.data["updated"] == 1
    assert Loan.objects.filter(tenant_id=tenant_id, status="overdue").count() == 1


@pytest.mark.django_db
def test_returning_twice_is_refused(librarian, tenant_id, books, student):
    loan = Loan.objects.create(
        tenant_id=tenant_id, book=books[0], student=student,
        due_on=TODAY, status="returned", returned_on=TODAY,
    )
    resp = librarian.post(f"/api/v1/library/loans/{loan.id}/return_book/", {}, format="json")
    assert resp.status_code == 400
