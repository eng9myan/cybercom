"""
Credit notes and the defaulter escalation ladder.

A credit note says the money was never owed; a refund gives money back. The
tests below mostly guard that distinction, and the ladder's ordering — because
a school chasing a family over their children's schooling has to be able to
show exactly what it did and when.
"""

import uuid
from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from products.cyed.billing import collections
from products.cyed.billing.models import (
    BillLineItem,
    CreditNote,
    DunningCase,
    FeePlan,
    StudentBill,
)
from products.cyed.billing.services import generate_installments, record_payment
from products.cyed.notifications.models import Notification
from products.cyed.sis.models import Family, Guardian, Student


@pytest.fixture
def client_for(mint_token, mock_jwks, tenant_id):
    def _make(roles, email="bursar@cyed.edu.au"):
        c = APIClient()
        c.credentials(HTTP_AUTHORIZATION=f"Bearer {mint_token({
            'sub': str(uuid.uuid4()), 'email': email, 'tenant_id': str(tenant_id),
            'realm_access': {'roles': roles},
        })}")
        return c
    return _make


@pytest.fixture
def finance(client_for):
    return client_for(["finance"])


@pytest.fixture
def household(tenant_id):
    family = Family.objects.create(tenant_id=tenant_id, name="Tran Household")
    guardian = Guardian.objects.create(
        tenant_id=tenant_id, family=family, first_name="Hoa", last_name="Tran",
        email="hoa@example.com", phone="0400111222",
    )
    family.billing_contact = guardian
    family.save(update_fields=["billing_contact"])
    student = Student.objects.create(
        tenant_id=tenant_id, family=family, first_name="Mia", last_name="Tran",
        year_level=8, enrolment_status="enrolled",
    )
    return family, student


@pytest.fixture
def bill(tenant_id, household):
    _family, student = household
    plan = FeePlan.objects.create(
        tenant_id=tenant_id, name="Termly", schedule_type="termly", installments_count=3
    )
    b = StudentBill.objects.create(
        tenant_id=tenant_id, student=student, plan=plan, status="draft"
    )
    BillLineItem.objects.create(
        tenant_id=tenant_id, bill=b, category="tuition", description="Tuition",
        amount=Decimal("3000.00"),
    )
    generate_installments(b)
    return b


def _draft(tenant_id, student, bill, amount="500.00", **extra):
    return CreditNote.objects.create(
        tenant_id=tenant_id, student=student, bill=bill,
        amount=Decimal(amount), reason="remission", **extra,
    )


# ── credit notes ─────────────────────────────────────────────────────────────
@pytest.mark.django_db
def test_issuing_a_credit_note_reduces_the_balance(finance, tenant_id, household, bill):
    _family, student = household
    note = _draft(tenant_id, student, bill, "600.00")

    resp = finance.post(f"/api/v1/billing/credit-notes/{note.id}/issue/", {}, format="json")
    assert resp.status_code == 200, resp.data

    bill.refresh_from_db()
    assert bill.balance == Decimal("2400.00")
    note.refresh_from_db()
    assert note.status == "issued"
    assert note.number.startswith("CN-")
    assert note.issued_by == "bursar@cyed.edu.au"


@pytest.mark.django_db
def test_the_original_billed_figure_survives_the_credit(finance, tenant_id, household, bill):
    """
    The whole reason a credit note exists rather than an edit: what was billed
    stays visible next to what changed.
    """
    _family, student = household
    note = _draft(tenant_id, student, bill, "600.00")
    finance.post(f"/api/v1/billing/credit-notes/{note.id}/issue/", {}, format="json")

    bill.refresh_from_db()
    assert sum(i.amount_due for i in bill.installments.all()) == Decimal("3000.00")
    assert bill.balance == Decimal("2400.00")


@pytest.mark.django_db
def test_crediting_more_than_is_owed_is_refused(finance, tenant_id, household, bill):
    """Crediting past zero would turn the fee ledger into a source of funds."""
    _family, student = household
    note = _draft(tenant_id, student, bill, "5000.00")
    resp = finance.post(f"/api/v1/billing/credit-notes/{note.id}/issue/", {}, format="json")
    assert resp.status_code == 409
    assert "would put the account in funds" in resp.data["detail"]
    bill.refresh_from_db()
    assert bill.balance == Decimal("3000.00")


@pytest.mark.django_db
def test_a_credit_lands_on_the_oldest_unpaid_installment(finance, tenant_id, household, bill):
    """A family expects a credit to clear the debt they are being chased for."""
    _family, student = household
    note = _draft(tenant_id, student, bill, "400.00")
    finance.post(f"/api/v1/billing/credit-notes/{note.id}/issue/", {}, format="json")

    first = bill.installments.order_by("installment_no").first()
    assert first.balance == Decimal("600.00")   # 1000 − 400


@pytest.mark.django_db
def test_credit_after_partial_payment_respects_what_is_left(
    finance, tenant_id, household, bill
):
    _family, student = household
    record_payment(
        bill.installments.order_by("installment_no").first(), amount=Decimal("2500.00")
    )
    bill.refresh_from_db()
    assert bill.balance == Decimal("500.00")

    note = _draft(tenant_id, student, bill, "600.00")
    resp = finance.post(f"/api/v1/billing/credit-notes/{note.id}/issue/", {}, format="json")
    assert resp.status_code == 409


@pytest.mark.django_db
def test_an_issued_note_cannot_be_edited_or_deleted(finance, tenant_id, household, bill):
    _family, student = household
    note = _draft(tenant_id, student, bill)
    finance.post(f"/api/v1/billing/credit-notes/{note.id}/issue/", {}, format="json")

    patched = finance.patch(
        f"/api/v1/billing/credit-notes/{note.id}/", {"amount": "10.00"}, format="json"
    )
    assert patched.status_code == 409
    assert finance.delete(f"/api/v1/billing/credit-notes/{note.id}/").status_code == 409


@pytest.mark.django_db
def test_a_draft_is_still_editable(finance, tenant_id, household, bill):
    _family, student = household
    note = _draft(tenant_id, student, bill)
    resp = finance.patch(
        f"/api/v1/billing/credit-notes/{note.id}/", {"amount": "250.00"}, format="json"
    )
    assert resp.status_code == 200


@pytest.mark.django_db
def test_cancelling_restores_the_balance_and_needs_a_reason(
    finance, tenant_id, household, bill
):
    _family, student = household
    note = _draft(tenant_id, student, bill, "600.00")
    finance.post(f"/api/v1/billing/credit-notes/{note.id}/issue/", {}, format="json")

    bare = finance.post(f"/api/v1/billing/credit-notes/{note.id}/cancel/", {}, format="json")
    assert bare.status_code == 409
    assert "reason" in bare.data["detail"]

    resp = finance.post(
        f"/api/v1/billing/credit-notes/{note.id}/cancel/",
        {"reason": "Issued against the wrong student"}, format="json",
    )
    assert resp.status_code == 200
    bill.refresh_from_db()
    assert bill.balance == Decimal("3000.00")


@pytest.mark.django_db
def test_issuing_twice_is_refused(finance, tenant_id, household, bill):
    _family, student = household
    note = _draft(tenant_id, student, bill)
    finance.post(f"/api/v1/billing/credit-notes/{note.id}/issue/", {}, format="json")
    again = finance.post(f"/api/v1/billing/credit-notes/{note.id}/issue/", {}, format="json")
    assert again.status_code == 409


@pytest.mark.django_db
def test_a_note_naming_a_different_student_from_its_bill_is_refused(
    finance, tenant_id, household, bill
):
    stranger = Student.objects.create(
        tenant_id=tenant_id, first_name="Someone", last_name="Else", year_level=9
    )
    resp = finance.post("/api/v1/billing/credit-notes/", {
        "student": str(stranger.id), "bill": str(bill.id),
        "amount": "100.00", "reason": "goodwill",
    }, format="json")
    assert resp.status_code == 400


@pytest.mark.django_db
def test_a_parent_cannot_issue_themselves_a_credit(client_for, tenant_id, household, bill):
    _family, student = household
    note = _draft(tenant_id, student, bill)
    parent = client_for(["parent"], "hoa@example.com")
    assert parent.post(
        f"/api/v1/billing/credit-notes/{note.id}/issue/", {}, format="json"
    ).status_code == 403


# ── dunning ladder ───────────────────────────────────────────────────────────
@pytest.fixture
def overdue_case(tenant_id, household, bill):
    """A household with a genuinely overdue installment and an open case."""
    family, _student = household
    bill.installments.update(
        due_date=timezone.localdate() - timedelta(days=30), status="overdue"
    )
    return collections.open_cases(tenant_id)[0]


@pytest.mark.django_db
def test_sweep_opens_a_case_for_an_overdue_household(finance, tenant_id, household, bill):
    family, _student = household
    bill.installments.update(
        due_date=timezone.localdate() - timedelta(days=30), status="overdue"
    )
    resp = finance.post("/api/v1/billing/dunning-cases/sweep/", {}, format="json")
    assert resp.data["opened"] == 1
    case = DunningCase.objects.get(family=family)
    assert case.stage == 0 and case.status == "open"


@pytest.mark.django_db
def test_sweep_does_not_chase_a_household_that_owes_nothing(finance, tenant_id, household):
    resp = finance.post("/api/v1/billing/dunning-cases/sweep/", {}, format="json")
    assert resp.data["opened"] == 0


@pytest.mark.django_db
def test_sweep_never_opens_two_cases_for_one_household(finance, tenant_id, overdue_case):
    resp = finance.post("/api/v1/billing/dunning-cases/sweep/", {}, format="json")
    assert resp.data["opened"] == 0


@pytest.mark.django_db
def test_escalating_climbs_one_rung_and_notifies(finance, tenant_id, overdue_case):
    resp = finance.post(
        f"/api/v1/billing/dunning-cases/{overdue_case.id}/escalate/", {}, format="json"
    )
    assert resp.status_code == 201, resp.data
    overdue_case.refresh_from_db()
    assert overdue_case.stage == 1

    note = Notification.objects.filter(tenant_id=tenant_id, category="billing").first()
    assert note is not None
    assert note.recipient_email == "hoa@example.com"
    assert note.subject == "Fee reminder"


@pytest.mark.django_db
def test_the_ladder_cannot_be_climbed_twice_in_a_day(finance, overdue_case):
    """Escalating faster than a family can respond is harassment, not process."""
    finance.post(f"/api/v1/billing/dunning-cases/{overdue_case.id}/escalate/", {}, format="json")
    second = finance.post(
        f"/api/v1/billing/dunning-cases/{overdue_case.id}/escalate/", {}, format="json"
    )
    assert second.status_code == 409
    assert "Wait" in second.data["detail"]


@pytest.mark.django_db
def test_rungs_are_climbed_in_order_and_stop_at_referral(finance, overdue_case):
    for expected_stage in (1, 2, 3, 4):
        overdue_case.last_action_on = timezone.localdate() - timedelta(days=8)
        overdue_case.save(update_fields=["last_action_on"])
        resp = finance.post(
            f"/api/v1/billing/dunning-cases/{overdue_case.id}/escalate/", {}, format="json"
        )
        assert resp.status_code == 201, resp.data
        assert resp.data["stage"] == expected_stage

    overdue_case.last_action_on = timezone.localdate() - timedelta(days=8)
    overdue_case.save(update_fields=["last_action_on"])
    beyond = finance.post(
        f"/api/v1/billing/dunning-cases/{overdue_case.id}/escalate/", {}, format="json"
    )
    assert beyond.status_code == 409
    assert "final stage" in beyond.data["detail"]


@pytest.mark.django_db
def test_every_rung_is_recorded_with_who_and_when(finance, overdue_case):
    finance.post(f"/api/v1/billing/dunning-cases/{overdue_case.id}/escalate/", {
        "note": "Reminder emailed to billing contact",
    }, format="json")
    action = overdue_case.actions.first()
    assert action.performed_by == "bursar@cyed.edu.au"
    assert action.balance_at_action > 0
    assert "Reminder emailed" in action.note


@pytest.mark.django_db
def test_a_paused_case_stops_receiving_letters(finance, overdue_case):
    """A family already talking to the school should not keep getting notices."""
    paused = finance.post(f"/api/v1/billing/dunning-cases/{overdue_case.id}/pause/", {
        "until": (timezone.localdate() + timedelta(days=30)).isoformat(),
        "reason": "Payment plan under discussion",
    }, format="json")
    assert paused.status_code == 200

    resp = finance.post(
        f"/api/v1/billing/dunning-cases/{overdue_case.id}/escalate/", {}, format="json"
    )
    assert resp.status_code == 409
    assert "paused until" in resp.data["detail"]


@pytest.mark.django_db
def test_a_resumed_case_can_escalate_again(finance, overdue_case):
    finance.post(f"/api/v1/billing/dunning-cases/{overdue_case.id}/pause/", {
        "reason": "Talking"
    }, format="json")
    finance.post(f"/api/v1/billing/dunning-cases/{overdue_case.id}/resume/", {}, format="json")

    overdue_case.refresh_from_db()
    overdue_case.last_action_on = timezone.localdate() - timedelta(days=8)
    overdue_case.save(update_fields=["last_action_on"])
    resp = finance.post(
        f"/api/v1/billing/dunning-cases/{overdue_case.id}/escalate/", {}, format="json"
    )
    assert resp.status_code == 201


@pytest.mark.django_db
def test_escalating_a_settled_household_is_refused(finance, tenant_id, overdue_case, bill):
    for installment in bill.installments.all():
        record_payment(installment, amount=installment.balance)
    overdue_case.last_action_on = timezone.localdate() - timedelta(days=8)
    overdue_case.save(update_fields=["last_action_on"])

    resp = finance.post(
        f"/api/v1/billing/dunning-cases/{overdue_case.id}/escalate/", {}, format="json"
    )
    assert resp.status_code == 409
    assert "nothing overdue" in resp.data["detail"]


@pytest.mark.django_db
def test_sweep_closes_cases_once_the_family_has_paid(finance, tenant_id, overdue_case, bill):
    for installment in bill.installments.all():
        record_payment(installment, amount=installment.balance)
    resp = finance.post("/api/v1/billing/dunning-cases/sweep/", {}, format="json")
    assert resp.data["resolved"] == 1
    overdue_case.refresh_from_db()
    assert overdue_case.status == "resolved"


@pytest.mark.django_db
def test_a_debt_can_be_written_off_distinctly_from_being_paid(finance, overdue_case):
    resp = finance.post(f"/api/v1/billing/dunning-cases/{overdue_case.id}/resolve/", {
        "written_off": True, "note": "Hardship — approved by principal",
    }, format="json")
    assert resp.status_code == 200
    overdue_case.refresh_from_db()
    assert overdue_case.status == "written_off"


@pytest.mark.django_db
def test_the_sweep_does_not_query_per_household(django_assert_max_num_queries, tenant_id):
    """
    Built the obvious way — a full statement per family to read one number —
    this took 104 seconds and over 9,000 queries against a seeded year. A
    nightly job that slow stops being run, so the query count is pinned.
    """
    from products.cyed.billing.services import generate_installments

    plan = FeePlan.objects.create(
        tenant_id=tenant_id, name="Termly", schedule_type="upfront", installments_count=1
    )
    for i in range(25):
        family = Family.objects.create(tenant_id=tenant_id, name=f"Household {i}")
        student = Student.objects.create(
            tenant_id=tenant_id, family=family, first_name=f"S{i}", last_name="Test",
            year_level=8, enrolment_status="enrolled",
        )
        bill = StudentBill.objects.create(
            tenant_id=tenant_id, student=student, plan=plan, status="draft"
        )
        BillLineItem.objects.create(
            tenant_id=tenant_id, bill=bill, category="tuition", amount=Decimal("1000.00")
        )
        generate_installments(bill)
        bill.installments.update(
            due_date=timezone.localdate() - timedelta(days=30), status="overdue"
        )

    # Flat in the number of households: a handful of aggregates plus the
    # inserts. Nowhere near one query per family.
    with django_assert_max_num_queries(15):
        opened = collections.open_cases(tenant_id)
    assert len(opened) == 25


@pytest.mark.django_db
def test_bulk_totals_agree_with_the_per_household_statement(tenant_id, household, bill):
    """
    Two views of the same debt must not disagree — including by a trailing
    zero, which a bursar will report as a bug.
    """
    from products.cyed.billing.family_accounts import family_statement, family_totals_bulk

    family, _student = household
    bill.installments.update(
        due_date=timezone.localdate() - timedelta(days=30), status="overdue"
    )
    statement = family_statement(family)
    bulk = family_totals_bulk(tenant_id)[str(family.id)]

    assert str(bulk["balance"]) == statement["totals"]["balance"]
    assert str(bulk["overdue"]) == statement["totals"]["overdue"]


@pytest.mark.django_db
def test_the_stage_cannot_be_jumped_by_posting_a_case(finance, tenant_id, household):
    family, _student = household
    resp = finance.post("/api/v1/billing/dunning-cases/", {
        "family": str(family.id), "stage": 4,
    }, format="json")
    assert resp.status_code == 405
