"""
Staff compliance: clearance expiry and leave balances.

The two questions HR is asked most — "is this person's clearance current?" and
"does she have leave left?" — and, more importantly, the two enforcement points
behind them. A system that only displays the problem has not met the
obligation.
"""

import uuid
from datetime import date, timedelta
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from products.cyed.hr import compliance
from products.cyed.hr.models import Contract, LeaveEntitlement, Staff, StaffClearance, StaffLeave
from products.cyed.sis.models import ClassSection

TODAY = date(2026, 8, 11)


@pytest.fixture
def client_for(mint_token, mock_jwks, tenant_id):
    def _make(roles, email="user@cyed.edu.au"):
        token = mint_token({
            "sub": str(uuid.uuid4()), "email": email, "tenant_id": str(tenant_id),
            "realm_access": {"roles": roles},
        })
        c = APIClient()
        c.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        return c
    return _make


@pytest.fixture
def leadership(client_for):
    return client_for(["leadership"], email="principal@cyed.edu.au")


@pytest.fixture
def teacher(tenant_id):
    return Staff.objects.create(
        tenant_id=tenant_id, first_name="Anh", last_name="Nguyen",
        role="teacher", email="anh@cyed.edu.au",
    )


def _clear(staff, kind, *, expires, verified=True):
    return StaffClearance.objects.create(
        tenant_id=staff.tenant_id, staff=staff, kind=kind, number="X123",
        issuing_state="VIC", issued_on=TODAY - timedelta(days=365),
        expires_on=expires,
        verified_on=TODAY - timedelta(days=365) if verified else None,
        verified_by="registrar@cyed.edu.au" if verified else "",
    )


def _fully_cleared(staff, expires=None):
    expires = expires or TODAY + timedelta(days=365)
    _clear(staff, "wwcc", expires=expires)
    _clear(staff, "teacher_registration", expires=expires)


# ── clearance status ─────────────────────────────────────────────────────────
@pytest.mark.django_db
def test_a_current_clearance_is_valid(teacher):
    c = _clear(teacher, "wwcc", expires=TODAY + timedelta(days=365))
    assert c.status(TODAY) == "valid"
    assert c.is_current(TODAY)


@pytest.mark.django_db
def test_a_lapsed_clearance_is_expired(teacher):
    c = _clear(teacher, "wwcc", expires=TODAY - timedelta(days=1))
    assert c.status(TODAY) == "expired"
    assert not c.is_current(TODAY)


@pytest.mark.django_db
def test_a_clearance_inside_the_renewal_window_is_flagged_but_still_valid(teacher):
    """Six weeks' warning is roughly the turnaround on a WWCC renewal."""
    c = _clear(teacher, "wwcc", expires=TODAY + timedelta(days=20))
    assert c.status(TODAY) == "expiring"
    assert c.is_current(TODAY)  # still allowed in a classroom


@pytest.mark.django_db
def test_an_unverified_clearance_is_not_evidence_of_anything(teacher):
    """A number typed in without anyone sighting the card proves nothing."""
    c = _clear(teacher, "wwcc", expires=TODAY + timedelta(days=365), verified=False)
    assert c.status(TODAY) == "unverified"
    assert not c.is_current(TODAY)


@pytest.mark.django_db
def test_a_credential_with_no_expiry_stays_valid(teacher):
    c = _clear(teacher, "police_check", expires=None)
    assert c.status(TODAY) == "valid"


# ── the enforcement point ────────────────────────────────────────────────────
@pytest.mark.django_db
def test_missing_clearance_blocks_teaching_exactly_like_an_expired_one(teacher):
    """
    Absence of evidence is not evidence of a clearance. A school that never
    recorded a WWCC is in the same position as one whose record lapsed.
    """
    state = compliance.clearance_state(teacher, TODAY)
    assert state["may_teach"] is False
    assert {b["kind"] for b in state["blocking"]} == {"wwcc", "teacher_registration"}
    assert all(b["reason"] == "missing" for b in state["blocking"])


@pytest.mark.django_db
def test_fully_cleared_staff_may_teach(teacher):
    _fully_cleared(teacher)
    assert compliance.clearance_state(teacher, TODAY)["may_teach"] is True


@pytest.mark.django_db
def test_expired_wwcc_blocks_a_class_assignment(leadership, tenant_id, teacher):
    _fully_cleared(teacher)
    teacher.clearances.filter(kind="wwcc").update(expires_on=TODAY - timedelta(days=1))

    resp = leadership.post("/api/v1/sis/class-sections/", {
        "name": "8A Mathematics", "year_level": 8, "teacher": str(teacher.id),
    }, format="json")
    assert resp.status_code == 400
    assert "Working With Children Check" in str(resp.data)


@pytest.mark.django_db
def test_expired_registration_blocks_a_timetable_assignment(leadership, tenant_id, teacher):
    _fully_cleared(teacher)
    teacher.clearances.filter(kind="teacher_registration").update(
        expires_on=TODAY - timedelta(days=1)
    )
    section = ClassSection.objects.create(tenant_id=tenant_id, name="8A", year_level=8)

    resp = leadership.post("/api/v1/timetable/slots/", {
        "class_section": str(section.id), "day_of_week": "mon", "period_label": "P1",
        "start_time": "09:00:00", "end_time": "10:00:00", "teacher": str(teacher.id),
    }, format="json")
    assert resp.status_code == 400
    assert "Teacher Registration" in str(resp.data)


@pytest.mark.django_db
def test_a_cleared_teacher_can_be_assigned(leadership, tenant_id, teacher):
    _fully_cleared(teacher)
    resp = leadership.post("/api/v1/sis/class-sections/", {
        "name": "8A Mathematics", "year_level": 8, "teacher": str(teacher.id),
    }, format="json")
    assert resp.status_code == 201, resp.data


# ── the registrar's worklist ─────────────────────────────────────────────────
@pytest.mark.django_db
def test_expiring_worklist_puts_expired_first(tenant_id, leadership):
    lapsed = Staff.objects.create(tenant_id=tenant_id, first_name="Lapsed", last_name="One")
    soon = Staff.objects.create(tenant_id=tenant_id, first_name="Soon", last_name="Two")
    fine = Staff.objects.create(tenant_id=tenant_id, first_name="Fine", last_name="Three")
    _clear(lapsed, "wwcc", expires=TODAY - timedelta(days=5))
    _clear(soon, "wwcc", expires=TODAY + timedelta(days=10))
    _clear(fine, "wwcc", expires=TODAY + timedelta(days=900))

    rows = compliance.expiring_clearances(tenant_id, as_at=TODAY)
    assert [r["name"] for r in rows] == ["Lapsed One", "Soon Two"]
    assert rows[0]["status"] == "expired"
    assert rows[0]["blocks_teaching"] is True


@pytest.mark.django_db
def test_departed_staff_are_not_chased(tenant_id):
    """Chasing a renewal from someone who resigned hides the real cases."""
    gone = Staff.objects.create(
        tenant_id=tenant_id, first_name="Gone", last_name="Away", is_active=False
    )
    _clear(gone, "wwcc", expires=TODAY - timedelta(days=5))
    assert compliance.expiring_clearances(tenant_id, as_at=TODAY) == []


@pytest.mark.django_db
def test_blocked_from_teaching_lists_the_classes_that_need_covering(
    leadership, tenant_id, teacher
):
    _fully_cleared(teacher)
    ClassSection.objects.create(
        tenant_id=tenant_id, name="8A Mathematics", year_level=8, teacher=teacher
    )
    teacher.clearances.filter(kind="wwcc").update(expires_on=TODAY - timedelta(days=1))

    resp = leadership.get("/api/v1/hr/clearances/blocked-from-teaching/")
    assert resp.status_code == 200
    assert resp.data["count"] == 1
    assert resp.data["results"][0]["class_sections"] == ["8A Mathematics"]


@pytest.mark.django_db
def test_staff_cannot_verify_their_own_clearance(client_for, tenant_id, teacher):
    """The value of the record is that a responsible person sighted the card."""
    own = client_for(["teacher"], email="anh@cyed.edu.au")
    resp = own.post("/api/v1/hr/clearances/", {
        "staff": str(teacher.id), "kind": "wwcc", "number": "SELF1",
        "expires_on": (TODAY + timedelta(days=365)).isoformat(),
        "verified_on": TODAY.isoformat(),
    }, format="json")
    assert resp.status_code == 403


@pytest.mark.django_db
def test_verifier_is_stamped_from_the_authenticated_user(leadership, tenant_id, teacher):
    resp = leadership.post("/api/v1/hr/clearances/", {
        "staff": str(teacher.id), "kind": "wwcc", "number": "A1",
        "expires_on": (TODAY + timedelta(days=365)).isoformat(),
        "verified_on": TODAY.isoformat(),
        "verified_by": "someone.else@example.com",   # must be ignored
    }, format="json")
    assert resp.status_code == 201, resp.data
    assert resp.data["verified_by"] == "principal@cyed.edu.au"


@pytest.mark.django_db
def test_expiry_before_issue_is_refused(leadership, teacher):
    resp = leadership.post("/api/v1/hr/clearances/", {
        "staff": str(teacher.id), "kind": "wwcc",
        "issued_on": TODAY.isoformat(),
        "expires_on": (TODAY - timedelta(days=1)).isoformat(),
    }, format="json")
    assert resp.status_code == 400


# ── leave entitlements ───────────────────────────────────────────────────────
@pytest.mark.django_db
def test_full_time_staff_get_the_nes_entitlement(tenant_id, teacher):
    Contract.objects.create(
        tenant_id=tenant_id, staff=teacher, contract_type="full_time",
        annual_salary=Decimal("96000"), fte=Decimal("1"), is_current=True,
    )
    compliance.ensure_entitlements(teacher, 2026)
    annual = LeaveEntitlement.objects.get(staff=teacher, leave_type="annual", year=2026)
    sick = LeaveEntitlement.objects.get(staff=teacher, leave_type="sick", year=2026)
    assert annual.entitled_days == Decimal("20.00")   # 4 weeks
    assert sick.entitled_days == Decimal("10.00")


@pytest.mark.django_db
def test_part_time_entitlement_is_pro_rated_by_fte(tenant_id, teacher):
    Contract.objects.create(
        tenant_id=tenant_id, staff=teacher, contract_type="part_time",
        fte=Decimal("0.6"), is_current=True,
    )
    compliance.ensure_entitlements(teacher, 2026)
    assert LeaveEntitlement.objects.get(
        staff=teacher, leave_type="annual", year=2026
    ).entitled_days == Decimal("12.00")


@pytest.mark.django_db
def test_casuals_accrue_no_paid_leave(tenant_id, teacher):
    """Under the NES a casual is paid a loading in lieu of paid leave."""
    Contract.objects.create(
        tenant_id=tenant_id, staff=teacher, contract_type="casual",
        hourly_rate=Decimal("60"), is_current=True,
    )
    compliance.ensure_entitlements(teacher, 2026)
    assert LeaveEntitlement.objects.get(
        staff=teacher, leave_type="annual", year=2026
    ).entitled_days == Decimal("0.00")


@pytest.mark.django_db
def test_opening_a_year_twice_is_harmless(tenant_id, teacher):
    Contract.objects.create(tenant_id=tenant_id, staff=teacher, fte=Decimal("1"), is_current=True)
    assert len(compliance.ensure_entitlements(teacher, 2026)) == 2
    assert len(compliance.ensure_entitlements(teacher, 2026)) == 0


@pytest.mark.django_db
def test_a_hand_adjusted_entitlement_is_not_overwritten(tenant_id, teacher):
    Contract.objects.create(tenant_id=tenant_id, staff=teacher, fte=Decimal("1"), is_current=True)
    LeaveEntitlement.objects.create(
        tenant_id=tenant_id, staff=teacher, leave_type="annual", year=2026,
        entitled_days=Decimal("25.00"), notes="Negotiated in contract",
    )
    compliance.ensure_entitlements(teacher, 2026)
    assert LeaveEntitlement.objects.get(
        staff=teacher, leave_type="annual", year=2026
    ).entitled_days == Decimal("25.00")


@pytest.mark.django_db
def test_leave_accrues_progressively_not_all_on_1_january(tenant_id, teacher):
    """
    Approving against the full annual figure in February is how a school pays
    out leave that was never earned when someone resigns in March.
    """
    ent = LeaveEntitlement.objects.create(
        tenant_id=tenant_id, staff=teacher, leave_type="annual", year=2026,
        entitled_days=Decimal("20.00"),
    )
    assert ent.accrued_days(date(2026, 1, 1)) < Decimal("0.10")
    assert ent.accrued_days(date(2026, 7, 1)) == pytest.approx(Decimal("9.92"), abs=Decimal("0.1"))
    assert ent.accrued_days(date(2026, 12, 31)) == Decimal("20.00")
    assert ent.accrued_days(date(2027, 3, 1)) == Decimal("20.00")


@pytest.mark.django_db
def test_balance_is_derived_from_approved_leave(tenant_id, teacher):
    ent = LeaveEntitlement.objects.create(
        tenant_id=tenant_id, staff=teacher, leave_type="annual", year=2026,
        entitled_days=Decimal("20.00"), opening_balance=Decimal("5.00"),
    )
    StaffLeave.objects.create(
        tenant_id=tenant_id, staff=teacher, leave_type="annual", status="approved",
        start_date=date(2026, 3, 2), end_date=date(2026, 3, 6), days=Decimal("5.0"),
    )
    # A rejected request must not consume balance.
    StaffLeave.objects.create(
        tenant_id=tenant_id, staff=teacher, leave_type="annual", status="rejected",
        start_date=date(2026, 4, 1), end_date=date(2026, 4, 3), days=Decimal("3.0"),
    )
    assert ent.taken_days() == Decimal("5.0")
    assert ent.balance(date(2026, 12, 31)) == Decimal("20.00")  # 5 + 20 − 5


# ── over-draw enforcement ────────────────────────────────────────────────────
@pytest.mark.django_db
def test_approving_more_leave_than_accrued_is_refused(leadership, tenant_id, teacher):
    LeaveEntitlement.objects.create(
        tenant_id=tenant_id, staff=teacher, leave_type="annual", year=2026,
        entitled_days=Decimal("20.00"),
    )
    leave = StaffLeave.objects.create(
        tenant_id=tenant_id, staff=teacher, leave_type="annual", status="requested",
        start_date=date(2026, 2, 2), end_date=date(2026, 2, 27), days=Decimal("20.0"),
    )
    resp = leadership.post(f"/api/v1/hr/leave/{leave.id}/approve/", {}, format="json")
    assert resp.status_code == 409
    assert "Insufficient leave balance" in resp.data["detail"]
    leave.refresh_from_db()
    assert leave.status == "requested"


@pytest.mark.django_db
def test_leadership_can_override_but_must_say_why(leadership, tenant_id, teacher):
    """
    Taking leave in advance of accrual is a normal arrangement — but it has to
    be deliberate and attributable. An override with no reason is
    indistinguishable from a bug six months later.
    """
    LeaveEntitlement.objects.create(
        tenant_id=tenant_id, staff=teacher, leave_type="annual", year=2026,
        entitled_days=Decimal("20.00"),
    )
    leave = StaffLeave.objects.create(
        tenant_id=tenant_id, staff=teacher, leave_type="annual", status="requested",
        start_date=date(2026, 2, 2), end_date=date(2026, 2, 27), days=Decimal("20.0"),
    )
    resp = leadership.post(
        f"/api/v1/hr/leave/{leave.id}/approve/",
        {"override_reason": "Leave in advance, agreed with principal"}, format="json",
    )
    assert resp.status_code == 200
    leave.refresh_from_db()
    assert leave.status == "approved"
    assert leave.balance_override_by == "principal@cyed.edu.au"
    assert "agreed with principal" in leave.balance_override_reason


@pytest.mark.django_db
def test_leave_within_balance_approves_normally(leadership, tenant_id, teacher):
    LeaveEntitlement.objects.create(
        tenant_id=tenant_id, staff=teacher, leave_type="annual", year=2026,
        entitled_days=Decimal("20.00"), opening_balance=Decimal("10.00"),
    )
    leave = StaffLeave.objects.create(
        tenant_id=tenant_id, staff=teacher, leave_type="annual", status="requested",
        start_date=date(2026, 3, 2), end_date=date(2026, 3, 6), days=Decimal("5.0"),
    )
    resp = leadership.post(f"/api/v1/hr/leave/{leave.id}/approve/", {}, format="json")
    assert resp.status_code == 200
    assert resp.data["status"] == "approved"


@pytest.mark.django_db
def test_unpaid_leave_is_not_blocked_by_a_balance(leadership, tenant_id, teacher):
    """Refusing unpaid leave on accrual grounds would deny an entitlement."""
    leave = StaffLeave.objects.create(
        tenant_id=tenant_id, staff=teacher, leave_type="unpaid", status="requested",
        start_date=date(2026, 3, 2), end_date=date(2026, 3, 27), days=Decimal("20.0"),
    )
    resp = leadership.post(f"/api/v1/hr/leave/{leave.id}/approve/", {}, format="json")
    assert resp.status_code == 200


@pytest.mark.django_db
def test_approving_with_no_entitlement_on_record_is_refused(leadership, tenant_id, teacher):
    """An unknowable balance is not the same as a sufficient one."""
    leave = StaffLeave.objects.create(
        tenant_id=tenant_id, staff=teacher, leave_type="annual", status="requested",
        start_date=date(2026, 3, 2), end_date=date(2026, 3, 6), days=Decimal("5.0"),
    )
    resp = leadership.post(f"/api/v1/hr/leave/{leave.id}/approve/", {}, format="json")
    assert resp.status_code == 409
    assert "No Annual entitlement exists for 2026" in resp.data["detail"]


# ── the API HR actually uses ─────────────────────────────────────────────────
@pytest.mark.django_db
def test_balances_endpoint_answers_does_she_have_leave_left(leadership, tenant_id, teacher):
    Contract.objects.create(tenant_id=tenant_id, staff=teacher, fte=Decimal("1"), is_current=True)
    compliance.ensure_entitlements(teacher, 2026)
    StaffLeave.objects.create(
        tenant_id=tenant_id, staff=teacher, leave_type="annual", status="approved",
        start_date=date(2026, 3, 2), end_date=date(2026, 3, 6), days=Decimal("5.0"),
    )
    resp = leadership.get(f"/api/v1/hr/leave-entitlements/balances/?staff={teacher.id}&year=2026")
    assert resp.status_code == 200
    annual = next(b for b in resp.data["balances"] if b["leave_type"] == "annual")
    # Compared numerically: the decimal places a database returns for a SUM are
    # a backend detail, not part of the contract.
    assert Decimal(annual["taken"]) == Decimal("5")
    assert Decimal(annual["entitled_days"]) == Decimal("20")
    assert Decimal(annual["balance"]) == Decimal(annual["opening_balance"]) + Decimal(
        annual["accrued_to_date"]
    ) - Decimal(annual["taken"])


@pytest.mark.django_db
def test_open_year_provisions_the_whole_school(leadership, tenant_id):
    for i in range(3):
        s = Staff.objects.create(tenant_id=tenant_id, first_name=f"S{i}", last_name="Teacher")
        Contract.objects.create(tenant_id=tenant_id, staff=s, fte=Decimal("1"), is_current=True)
    resp = leadership.post("/api/v1/hr/leave-entitlements/open-year/", {"year": 2026}, format="json")
    assert resp.status_code == 200
    assert resp.data["entitlements_created"] == 6  # annual + personal for each


@pytest.mark.django_db
def test_only_leadership_may_open_a_leave_year(client_for):
    resp = client_for(["teacher"]).post(
        "/api/v1/hr/leave-entitlements/open-year/", {"year": 2026}, format="json"
    )
    assert resp.status_code == 403
