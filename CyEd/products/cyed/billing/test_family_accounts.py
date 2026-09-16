"""
Sibling discounts and the consolidated family statement.

The cases that matter are the ones where a household *changes*: a third child
enrols, the eldest leaves, a child moves between households. Those are what
make sibling pricing hard, and what a per-student billing system gets wrong.
"""

import uuid
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from products.cyed.billing.models import BillLineItem, FeePlan, SiblingDiscountRule, StudentBill
from products.cyed.billing import family_accounts, services
from products.cyed.fees.models import Invoice
from products.cyed.sis.models import Family, Guardian, Student


def _client(mint_token, mock_jwks, tenant_id, roles, email):
    token = mint_token({
        "sub": str(uuid.uuid4()), "email": email,
        "tenant_id": str(tenant_id), "realm_access": {"roles": roles},
    })
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


@pytest.fixture
def finance_client(mint_token, mock_jwks, tenant_id):
    return _client(mint_token, mock_jwks, tenant_id, ["finance"], "bursar@cyed.edu.au")


@pytest.fixture
def parent_client(mint_token, mock_jwks, tenant_id):
    return _client(mint_token, mock_jwks, tenant_id, ["parent"], "parent@example.com")


@pytest.fixture
def other_parent_client(mint_token, mock_jwks, tenant_id):
    return _client(mint_token, mock_jwks, tenant_id, ["parent"], "stranger@example.com")


@pytest.fixture
def plan(tenant_id):
    return FeePlan.objects.create(
        tenant_id=tenant_id, name="Termly", schedule_type="termly", installments_count=3
    )


def _child(tenant_id, family, first, year, dob, status="enrolled"):
    return Student.objects.create(
        tenant_id=tenant_id, family=family, first_name=first, last_name="Nguyen",
        year_level=year, date_of_birth=dob, enrolment_status=status,
    )


def _bill(tenant_id, student, plan, tuition="3000.00", transport=None):
    bill = StudentBill.objects.create(
        tenant_id=tenant_id, student=student, plan=plan, status="draft"
    )
    BillLineItem.objects.create(
        tenant_id=tenant_id, bill=bill, category="tuition",
        description="Tuition", amount=Decimal(tuition),
    )
    if transport:
        BillLineItem.objects.create(
            tenant_id=tenant_id, bill=bill, category="transport",
            description="Bus", amount=Decimal(transport),
        )
    services.generate_installments(bill)
    return bill


@pytest.fixture
def household(tenant_id, plan):
    """Three enrolled children, eldest first: Year 10, Year 8, Year 5."""
    family = Family.objects.create(tenant_id=tenant_id, name="Nguyen Household")
    guardian = Guardian.objects.create(
        tenant_id=tenant_id, family=family, first_name="Lan", last_name="Nguyen",
        email="parent@example.com",
    )
    eldest = _child(tenant_id, family, "An", 10, "2010-03-01")
    middle = _child(tenant_id, family, "Binh", 8, "2012-05-01")
    youngest = _child(tenant_id, family, "Chi", 5, "2015-07-01")
    for s in (eldest, middle, youngest):
        s.guardians.add(guardian)
    return family, eldest, middle, youngest


@pytest.fixture
def rules(tenant_id):
    """Second child 10% off tuition; third and beyond 25%."""
    return [
        SiblingDiscountRule.objects.create(
            tenant_id=tenant_id, name="Second child", ordinal=2, percent=Decimal("10")
        ),
        SiblingDiscountRule.objects.create(
            tenant_id=tenant_id, name="Third child and beyond", ordinal=3, percent=Decimal("25")
        ),
    ]


# ── ordinals ─────────────────────────────────────────────────────────────────
@pytest.mark.django_db
def test_ordinals_are_eldest_first(household):
    _, eldest, middle, youngest = household
    assert family_accounts.sibling_ordinal(eldest) == 1
    assert family_accounts.sibling_ordinal(middle) == 2
    assert family_accounts.sibling_ordinal(youngest) == 3


@pytest.mark.django_db
def test_child_with_no_household_is_a_family_of_one(tenant_id):
    """Schools import students long before they tidy up households."""
    orphan = Student.objects.create(
        tenant_id=tenant_id, first_name="Solo", last_name="Student", year_level=7
    )
    assert family_accounts.sibling_ordinal(orphan) == 1


@pytest.mark.django_db
def test_withdrawn_child_does_not_occupy_an_ordinal(tenant_id, household, rules):
    """
    The leak this prevents: a graduated eldest keeps holding ordinal 1, so the
    family keeps a sibling discount it is no longer entitled to.
    """
    _, eldest, middle, youngest = household
    eldest.enrolment_status = "withdrawn"
    eldest.save(update_fields=["enrolment_status"])

    assert family_accounts.sibling_ordinal(middle) == 1
    assert family_accounts.sibling_ordinal(youngest) == 2


# ── rule resolution ──────────────────────────────────────────────────────────
@pytest.mark.django_db
def test_highest_rule_at_or_below_the_ordinal_wins(tenant_id, rules):
    """A rule at 3 covers the 4th and 5th child with no 'and beyond' flag."""
    assert family_accounts.resolve_rule(tenant_id, 1) is None
    assert family_accounts.resolve_rule(tenant_id, 2).percent == Decimal("10")
    assert family_accounts.resolve_rule(tenant_id, 3).percent == Decimal("25")
    assert family_accounts.resolve_rule(tenant_id, 7).percent == Decimal("25")


@pytest.mark.django_db
def test_campus_specific_rule_beats_the_group_wide_one(tenant_id, rules):
    from products.cyed.org.models import Campus

    campus = Campus.objects.create(tenant_id=tenant_id, name="Northside", code="NTH")
    SiblingDiscountRule.objects.create(
        tenant_id=tenant_id, name="Northside second child", ordinal=2,
        percent=Decimal("15"), campus=campus,
    )
    assert family_accounts.resolve_rule(tenant_id, 2).percent == Decimal("10")
    assert family_accounts.resolve_rule(tenant_id, 2, campus_id=campus.id).percent == Decimal("15")


# ── the money ────────────────────────────────────────────────────────────────
@pytest.mark.django_db
def test_discount_reduces_the_installment_schedule(tenant_id, household, rules, plan):
    _, eldest, middle, youngest = household
    b1 = _bill(tenant_id, eldest, plan)
    b2 = _bill(tenant_id, middle, plan)
    b3 = _bill(tenant_id, youngest, plan)

    # 3000 tuition: eldest full, 2nd −10% = 2700, 3rd −25% = 2250.
    assert sum(i.amount_due for i in b1.installments.all()) == Decimal("3000.00")
    assert sum(i.amount_due for i in b2.installments.all()) == Decimal("2700.00")
    assert sum(i.amount_due for i in b3.installments.all()) == Decimal("2250.00")


@pytest.mark.django_db
def test_discount_does_not_bite_on_transport(tenant_id, household, rules, plan):
    """
    A family getting 25% off the bus is a revenue leak. The rule's categories
    default to tuition only.
    """
    _, _eldest, middle, _youngest = household
    bill = _bill(tenant_id, middle, plan, tuition="3000.00", transport="800.00")
    # 3000 − 10% = 2700, plus 800 transport at full price.
    assert sum(i.amount_due for i in bill.installments.all()) == Decimal("3500.00")


@pytest.mark.django_db
def test_a_rule_can_be_widened_to_other_categories(tenant_id, household, plan):
    SiblingDiscountRule.objects.create(
        tenant_id=tenant_id, name="Everything", ordinal=2, percent=Decimal("50"),
        categories=["tuition", "transport"],
    )
    _, _eldest, middle, _youngest = household
    bill = _bill(tenant_id, middle, plan, tuition="1000.00", transport="200.00")
    assert sum(i.amount_due for i in bill.installments.all()) == Decimal("600.00")


@pytest.mark.django_db
def test_sibling_and_upfront_discounts_do_not_compound_on_full_tuition(tenant_id, household):
    """
    Order is deliberate: sibling first, upfront on what remains. Applying both
    to the full amount would give back more than either policy grants.
    """
    tenant, _eldest, middle, _youngest = household[0].tenant_id, *household[1:]
    SiblingDiscountRule.objects.create(
        tenant_id=tenant, name="Second child", ordinal=2, percent=Decimal("10")
    )
    upfront = FeePlan.objects.create(
        tenant_id=tenant, name="Upfront", schedule_type="upfront",
        upfront_discount_percent=Decimal("10"),
    )
    bill = _bill(tenant, middle, upfront, tuition="1000.00")
    # 1000 − 10% = 900, then − 10% = 810. Compounding onto 1000 would be 800.
    assert sum(i.amount_due for i in bill.installments.all()) == Decimal("810.00")


# ── household changes re-price siblings ──────────────────────────────────────
@pytest.mark.django_db
def test_enrolling_a_younger_child_does_not_disturb_the_elder(tenant_id, household, rules, plan):
    family, eldest, middle, _youngest = household
    b1 = _bill(tenant_id, eldest, plan)
    services.recalculate(b1)
    assert sum(i.amount_due for i in b1.installments.all()) == Decimal("3000.00")


@pytest.mark.django_db
def test_withdrawing_the_eldest_reprices_the_siblings_on_resync(tenant_id, household, rules, plan):
    """
    The case a per-student biller gets wrong: the eldest leaves, everyone moves
    up an ordinal, and the second child should now pay full fees.
    """
    family, eldest, middle, youngest = household
    b2 = _bill(tenant_id, middle, plan)
    b3 = _bill(tenant_id, youngest, plan)
    assert sum(i.amount_due for i in b2.installments.all()) == Decimal("2700.00")

    eldest.enrolment_status = "withdrawn"
    eldest.save(update_fields=["enrolment_status"])
    family_accounts.resync_family(family)

    b2.refresh_from_db()
    b3.refresh_from_db()
    assert sum(i.amount_due for i in b2.installments.all()) == Decimal("3000.00")  # now 1st
    assert sum(i.amount_due for i in b3.installments.all()) == Decimal("2700.00")  # now 2nd


@pytest.mark.django_db
def test_resync_never_claws_back_money_already_paid(tenant_id, household, rules, plan):
    """
    A mid-year re-price must land on the unpaid installments only. Rewriting a
    paid installment would make the ledger disagree with the bank.
    """
    family, eldest, middle, _youngest = household
    bill = _bill(tenant_id, middle, plan)          # 2700 over 3 → 900 each
    first = bill.installments.order_by("installment_no").first()
    services.record_payment(first, amount=Decimal("900.00"), method="bpay")

    eldest.enrolment_status = "withdrawn"
    eldest.save(update_fields=["enrolment_status"])
    family_accounts.resync_family(family)

    bill.refresh_from_db()
    first.refresh_from_db()
    assert first.amount_due == Decimal("900.00")   # paid installment untouched
    assert first.status == "paid"
    # Total still lands on the new full price of 3000.
    assert sum(i.amount_due for i in bill.installments.all()) == Decimal("3000.00")


# ── consolidated statement ───────────────────────────────────────────────────
@pytest.mark.django_db
def test_statement_totals_every_child_across_both_ledgers(tenant_id, household, rules, plan):
    """
    CyEd bills through installment plans *and* ad-hoc invoices. A statement
    showing one and not the other understates what a family owes — the single
    error a statement must never make.
    """
    family, eldest, middle, youngest = household
    _bill(tenant_id, eldest, plan)      # 3000
    _bill(tenant_id, middle, plan)      # 2700
    _bill(tenant_id, youngest, plan)    # 2250
    Invoice.objects.create(
        tenant_id=tenant_id, student=eldest, description="Excursion",
        amount=Decimal("150.00"), status="issued",
    )

    statement = family_accounts.family_statement(family)
    assert statement["children_total"] == 3
    assert statement["totals"]["billed"] == "8100.00"      # 7950 + 150
    assert statement["totals"]["paid"] == "0.00"
    assert statement["totals"]["balance"] == "8100.00"
    assert statement["totals"]["sibling_discount_applied"] == "1050.00"  # 300 + 750

    # Children listed eldest-first so ordinals read in the quoted order.
    assert [c["name"] for c in statement["children"]] == ["An Nguyen", "Binh Nguyen", "Chi Nguyen"]
    assert statement["children"][1]["sibling_discount"]["sibling_ordinal"] == 2
    assert statement["children"][1]["sibling_discount"]["rule"] == "Second child"


@pytest.mark.django_db
def test_statement_reflects_payments(tenant_id, household, rules, plan):
    family, eldest, _middle, _youngest = household
    bill = _bill(tenant_id, eldest, plan)
    services.record_payment(
        bill.installments.order_by("installment_no").first(), amount=Decimal("1000.00")
    )
    statement = family_accounts.family_statement(family)
    assert statement["totals"]["paid"] == "1000.00"
    assert statement["totals"]["balance"] == "2000.00"


# ── API + access control ─────────────────────────────────────────────────────
@pytest.mark.django_db
def test_parent_can_read_their_own_family_statement(parent_client, tenant_id, household, rules, plan):
    family, eldest, _middle, _youngest = household
    _bill(tenant_id, eldest, plan)
    resp = parent_client.get(f"/api/v1/billing/families/{family.id}/statement/")
    assert resp.status_code == 200, resp.data
    assert resp.data["totals"]["billed"] == "3000.00"


@pytest.mark.django_db
def test_parent_cannot_read_another_familys_statement(other_parent_client, household):
    family = household[0]
    resp = other_parent_client.get(f"/api/v1/billing/families/{family.id}/statement/")
    assert resp.status_code == 404


@pytest.mark.django_db
def test_parent_cannot_change_the_fee_structure(parent_client, tenant_id):
    resp = parent_client.post(
        "/api/v1/billing/sibling-discounts/",
        {"name": "Free for me", "ordinal": 1, "percent": "100"}, format="json",
    )
    assert resp.status_code == 403


@pytest.mark.django_db
def test_dunning_worklist_lists_owing_families_largest_first(
    finance_client, tenant_id, household, rules, plan
):
    family, eldest, middle, _youngest = household
    _bill(tenant_id, eldest, plan)
    _bill(tenant_id, middle, plan)

    settled = Family.objects.create(tenant_id=tenant_id, name="Paid Up Household")
    Student.objects.create(
        tenant_id=tenant_id, family=settled, first_name="Zoe", last_name="Clear", year_level=6
    )

    resp = finance_client.get("/api/v1/billing/families/")
    assert resp.status_code == 200
    names = [r["name"] for r in resp.data["results"]]
    assert names == ["Nguyen Household"]        # a family owing nothing is not chased
    assert resp.data["results"][0]["balance"] == "5700.00"

    everyone = finance_client.get("/api/v1/billing/families/?all=1")
    assert len(everyone.data["results"]) == 2


@pytest.mark.django_db
def test_typo_in_categories_is_rejected_rather_than_silently_zero(finance_client):
    """A category that matches no line item makes the discount vanish quietly."""
    resp = finance_client.post(
        "/api/v1/billing/sibling-discounts/",
        {"name": "Typo", "ordinal": 2, "percent": "10", "categories": ["tution"]},
        format="json",
    )
    assert resp.status_code == 400
    assert "Unknown line-item categories" in str(resp.data)


@pytest.mark.django_db
def test_apply_all_rolls_a_new_structure_onto_existing_bills(
    finance_client, tenant_id, household, plan
):
    """
    Rules are evaluated when a schedule is built, so existing bills keep their
    old numbers until something touches them. This is that something.
    """
    family, _eldest, middle, _youngest = household
    bill = _bill(tenant_id, middle, plan)
    assert sum(i.amount_due for i in bill.installments.all()) == Decimal("3000.00")

    SiblingDiscountRule.objects.create(
        tenant_id=tenant_id, name="Second child", ordinal=2, percent=Decimal("10")
    )
    resp = finance_client.post("/api/v1/billing/sibling-discounts/apply-all/", {}, format="json")
    assert resp.status_code == 200
    assert resp.data["bills_updated"] >= 1

    bill.refresh_from_db()
    assert sum(i.amount_due for i in bill.installments.all()) == Decimal("2700.00")


@pytest.mark.django_db
def test_attaching_a_child_to_a_household_reprices_that_household(
    mint_token, mock_jwks, tenant_id, household, rules, plan
):
    """End-to-end: the sis membership action must trigger the billing resync."""
    admin = _client(mint_token, mock_jwks, tenant_id, ["platform_admin"], "admin@cyed.edu.au")
    family, eldest, _middle, _youngest = household

    newcomer = Student.objects.create(
        tenant_id=tenant_id, first_name="Dao", last_name="Nguyen", year_level=12,
        date_of_birth="2008-01-01", enrolment_status="enrolled",
    )
    bill = _bill(tenant_id, newcomer, plan)
    assert sum(i.amount_due for i in bill.installments.all()) == Decimal("3000.00")

    resp = admin.post(
        f"/api/v1/sis/families/{family.id}/members/",
        {"students": [str(newcomer.id)], "guardians": []}, format="json",
    )
    assert resp.status_code == 200, resp.data

    # Dao is the eldest, so Dao stays at full price but everyone else shifts
    # down one ordinal — which is exactly why the resync has to be automatic.
    bill.refresh_from_db()
    assert sum(i.amount_due for i in bill.installments.all()) == Decimal("3000.00")
    assert family_accounts.sibling_ordinal(eldest) == 2


# ── The household record itself (sis), not just the money view ───────────────
@pytest.mark.django_db
def test_parent_can_read_their_own_household_record(parent_client, household):
    """
    The parent fee page loads the household before it can ask for a statement.
    Locking parents out of `sis/families/` entirely made their own fees screen
    fail with a bare permission error.
    """
    family = household[0]
    listed = parent_client.get("/api/v1/sis/families/")
    assert listed.status_code == 200, listed.data
    assert [f["id"] for f in listed.data["results"]] == [str(family.id)]

    detail = parent_client.get(f"/api/v1/sis/families/{family.id}/")
    assert detail.status_code == 200


@pytest.mark.django_db
def test_parent_cannot_read_another_household_record(other_parent_client, household):
    """A stranger's address and billing contact — 404, not 403, so the id is not confirmed."""
    family = household[0]
    listed = other_parent_client.get("/api/v1/sis/families/")
    assert listed.status_code == 200
    assert listed.data["results"] == []

    assert other_parent_client.get(f"/api/v1/sis/families/{family.id}/").status_code == 404


@pytest.mark.django_db
def test_parent_cannot_edit_a_household(parent_client, tenant_id, household):
    """
    Membership decides who is invoiced and who may collect a child. Read access
    for the portal must not have opened a write path.
    """
    family = household[0]
    outsider = Student.objects.create(
        tenant_id=tenant_id, first_name="Not", last_name="Mine", year_level=7,
        date_of_birth="2013-01-01", enrolment_status="enrolled",
    )
    assert parent_client.patch(
        f"/api/v1/sis/families/{family.id}/", {"name": "Renamed"}, format="json"
    ).status_code == 403
    assert parent_client.post(
        f"/api/v1/sis/families/{family.id}/members/",
        {"students": [str(outsider.id)], "guardians": []}, format="json",
    ).status_code == 403
    assert parent_client.post(
        "/api/v1/sis/families/", {"name": "My New Household"}, format="json"
    ).status_code == 403


@pytest.fixture
def student_client(mint_token, mock_jwks, tenant_id, household):
    """The eldest child, signed in as themselves."""
    eldest = household[1]
    eldest.email = "an@students.cyed.edu.au"
    eldest.save(update_fields=["email"])
    return _client(mint_token, mock_jwks, tenant_id, ["student"], eldest.email)


@pytest.mark.django_db
def test_a_student_cannot_read_the_family_finances(student_client, tenant_id, household, plan):
    """
    Scoping alone would admit a student — they can see themselves, so their
    household matches. Whether the fees are behind is between the school and
    the people paying, and a child should not find out through a portal.
    """
    family, eldest, _middle, _youngest = household
    _bill(tenant_id, eldest, plan)

    assert student_client.get("/api/v1/billing/families/").status_code == 403
    assert student_client.get(
        f"/api/v1/billing/families/{family.id}/statement/"
    ).status_code == 403
    assert student_client.get("/api/v1/billing/bills/").status_code == 403
    assert student_client.get("/api/v1/billing/installments/").status_code == 403


@pytest.mark.django_db
def test_a_student_can_still_read_their_own_schoolwork(student_client, household):
    """
    The control: without this, the assertions above would pass just as well if
    the student were locked out of everything.
    """
    assert student_client.get("/api/v1/sis/students/").status_code == 200
    assert student_client.get("/api/v1/gradebook/grades/").status_code == 200
