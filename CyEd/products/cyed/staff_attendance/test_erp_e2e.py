"""
End-to-end ERP tests: Staff Attendance → Payroll, HR workflows, Procurement →
Inventory → Accounting, financial statements, and Document Sign.

These exercise the modules the way the corresponding *roles* actually use them
(HR manager, payroll officer, procurement officer, accountant, staff member),
including permission boundaries and invalid input.
"""

import uuid
from datetime import date, timedelta
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from products.cyed.hr.models import Contract, Staff
from products.cyed.staff_attendance.models import StaffAttendanceDay


@pytest.fixture
def client_for(mint_token, mock_jwks, tenant_id):
    def _make(roles, email="user@cyed.edu.au"):
        token = mint_token({"sub": str(uuid.uuid4()), "email": email, "tenant_id": str(tenant_id),
                            "realm_access": {"roles": roles}})
        c = APIClient()
        c.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        return c
    return _make


@pytest.fixture
def teacher_staff(tenant_id):
    staff = Staff.objects.create(
        tenant_id=tenant_id, first_name="Ada", last_name="Lovelace",
        email="ada@cyed.edu.au", role="teacher", staff_number="T001",
    )
    Contract.objects.create(
        tenant_id=tenant_id, staff=staff, contract_type="full_time",
        annual_salary=Decimal("96000"), fte=Decimal("1"), is_current=True,
    )
    return staff


# ══════════════════ Staff Attendance ══════════════════
@pytest.mark.django_db
def test_staff_self_check_in_and_out(client_for, tenant_id, teacher_staff):
    """Staff member (general role): check in, then out — hours are derived."""
    me = client_for(["teacher"], email="ada@cyed.edu.au")
    r = me.post("/api/v1/staff-attendance/days/check-in/", {}, format="json")
    assert r.status_code == 200, r.data
    assert r.data["check_in"] is not None

    # Double check-in is rejected.
    again = me.post("/api/v1/staff-attendance/days/check-in/", {}, format="json")
    assert again.status_code == 400

    out = me.post("/api/v1/staff-attendance/days/check-out/", {}, format="json")
    assert out.status_code == 200, out.data
    assert out.data["check_out"] is not None


@pytest.mark.django_db
def test_check_out_before_check_in_rejected(client_for, tenant_id, teacher_staff):
    me = client_for(["teacher"], email="ada@cyed.edu.au")
    r = me.post("/api/v1/staff-attendance/days/check-out/", {}, format="json")
    assert r.status_code == 400
    assert "check" in r.data["detail"].lower()


@pytest.mark.django_db
def test_check_in_without_linked_staff_record(client_for, tenant_id):
    """A staff account with no matching Staff row gets a clear error, not a 500."""
    ghost = client_for(["teacher"], email="nobody@cyed.edu.au")
    r = ghost.post("/api/v1/staff-attendance/days/check-in/", {}, format="json")
    assert r.status_code == 400
    assert "staff record" in r.data["detail"].lower()


@pytest.mark.django_db
def test_lateness_is_computed(tenant_id, teacher_staff):
    from datetime import time

    day = StaffAttendanceDay.objects.create(
        tenant_id=tenant_id, staff=teacher_staff, date=date(2026, 3, 2),
        scheduled_start=time(8, 30), check_in=time(9, 5), check_out=time(16, 30),
    )
    assert day.minutes_late == 35
    assert day.status == "late"
    assert day.hours_worked == Decimal("7.42")  # 08:05 span


@pytest.mark.django_db
def test_staff_cannot_see_other_staff_attendance(client_for, tenant_id, teacher_staff):
    """RBAC: a teacher sees only their own days; leadership sees everyone."""
    other = Staff.objects.create(tenant_id=tenant_id, first_name="Bob", last_name="Other",
                                 email="bob@cyed.edu.au", role="teacher")
    StaffAttendanceDay.objects.create(tenant_id=tenant_id, staff=teacher_staff, date=date(2026, 3, 2))
    StaffAttendanceDay.objects.create(tenant_id=tenant_id, staff=other, date=date(2026, 3, 2))

    ada = client_for(["teacher"], email="ada@cyed.edu.au")
    rows = ada.get("/api/v1/staff-attendance/days/").data
    rows = rows["results"] if isinstance(rows, dict) else rows
    assert len(rows) == 1

    head = client_for(["principal"], email="head@cyed.edu.au")
    all_rows = head.get("/api/v1/staff-attendance/days/").data
    all_rows = all_rows["results"] if isinstance(all_rows, dict) else all_rows
    assert len(all_rows) == 2

    # Summary is leadership-only.
    assert ada.get("/api/v1/staff-attendance/days/summary/").status_code == 403
    assert head.get("/api/v1/staff-attendance/days/summary/").status_code == 200


@pytest.mark.django_db
def test_timesheet_rollup_and_approval(client_for, tenant_id, teacher_staff):
    for d, st in [(1, "present"), (2, "present"), (3, "absent"), (4, "sick")]:
        StaffAttendanceDay.objects.create(
            tenant_id=tenant_id, staff=teacher_staff, date=date(2026, 3, d), status=st
        )
    head = client_for(["principal"], email="head@cyed.edu.au")
    ts = head.post("/api/v1/staff-attendance/timesheets/", {
        "staff": str(teacher_staff.id), "period_label": "2026-03",
        "period_start": "2026-03-01", "period_end": "2026-03-31",
    }, format="json")
    assert ts.status_code == 201, ts.data

    detail = head.get(f"/api/v1/staff-attendance/timesheets/{ts.data['id']}/").data
    assert detail["days_present"] == 2
    assert detail["days_absent"] == 1
    assert detail["days_leave"] == 1

    # Approve requires a submitted timesheet.
    assert head.post(f"/api/v1/staff-attendance/timesheets/{ts.data['id']}/approve/").status_code == 400
    head.post(f"/api/v1/staff-attendance/timesheets/{ts.data['id']}/submit/")
    approved = head.post(f"/api/v1/staff-attendance/timesheets/{ts.data['id']}/approve/")
    assert approved.status_code == 200
    assert approved.data["status"] == "approved"

    # A teacher may not approve their own timesheet.
    ada = client_for(["teacher"], email="ada@cyed.edu.au")
    ts2 = head.post("/api/v1/staff-attendance/timesheets/", {
        "staff": str(teacher_staff.id), "period_label": "2026-04",
        "period_start": "2026-04-01", "period_end": "2026-04-30",
    }, format="json")
    ada.post(f"/api/v1/staff-attendance/timesheets/{ts2.data['id']}/submit/")
    assert ada.post(f"/api/v1/staff-attendance/timesheets/{ts2.data['id']}/approve/").status_code == 403


# ══════════════════ Payroll ← Staff Attendance ══════════════════
@pytest.mark.django_db
def test_payroll_docks_unpaid_absence_from_attendance(client_for, tenant_id, teacher_staff):
    """Payroll officer: an unexplained absence must reduce pay."""
    for d in range(2, 21):  # 19 working days present
        StaffAttendanceDay.objects.create(
            tenant_id=tenant_id, staff=teacher_staff, date=date(2026, 3, d), status="present"
        )
    StaffAttendanceDay.objects.create(
        tenant_id=tenant_id, staff=teacher_staff, date=date(2026, 3, 23), status="absent"
    )

    fin = client_for(["finance"], email="fin@cyed.edu.au")
    run = fin.post("/api/v1/payroll/runs/", {
        "period_label": "2026-03", "period_start": "2026-03-01", "period_end": "2026-03-31",
    }, format="json")
    assert run.status_code == 201, run.data
    proc = fin.post(f"/api/v1/payroll/runs/{run.data['id']}/process/")
    assert proc.status_code == 200, proc.data
    assert proc.data["payslips_created"] == 1

    slip = proc.data["payslips"][0]
    assert Decimal(slip["unpaid_days"]) == Decimal("1")
    assert Decimal(slip["unpaid_deduction"]) > 0
    # 96000/12 = 8000 base; one unpaid day at 8000/20 = 400 → gross 7600.
    assert Decimal(slip["gross"]) == Decimal("7600.00")
    kinds = {ln["kind"] for ln in slip["lines"]}
    assert {"earning", "deduction", "tax", "super"} <= kinds


@pytest.mark.django_db
def test_payroll_applies_allowances_and_deductions(client_for, tenant_id, teacher_staff):
    fin = client_for(["finance"], email="fin@cyed.edu.au")
    fin.post("/api/v1/payroll/salary-components/", {
        "staff": str(teacher_staff.id), "kind": "allowance",
        "description": "Laptop allowance", "amount": "150",
    }, format="json")
    fin.post("/api/v1/payroll/salary-components/", {
        "staff": str(teacher_staff.id), "kind": "deduction",
        "description": "Union fees", "amount": "40",
    }, format="json")

    run = fin.post("/api/v1/payroll/runs/", {"period_label": "2026-04"}, format="json")
    proc = fin.post(f"/api/v1/payroll/runs/{run.data['id']}/process/")
    slip = proc.data["payslips"][0]
    assert Decimal(slip["allowances_total"]) == Decimal("150.00")
    assert Decimal(slip["deductions_total"]) == Decimal("40.00")
    assert Decimal(slip["gross"]) == Decimal("8150.00")  # 8000 + allowance


@pytest.mark.django_db
def test_payroll_reconciles_against_attendance(client_for, tenant_id, teacher_staff):
    StaffAttendanceDay.objects.create(
        tenant_id=tenant_id, staff=teacher_staff, date=date(2026, 5, 4), status="present"
    )
    fin = client_for(["finance"], email="fin@cyed.edu.au")
    run = fin.post("/api/v1/payroll/runs/", {
        "period_label": "2026-05", "period_start": "2026-05-01", "period_end": "2026-05-31",
    }, format="json")
    fin.post(f"/api/v1/payroll/runs/{run.data['id']}/process/")

    rec = fin.get(f"/api/v1/payroll/runs/{run.data['id']}/reconcile/")
    assert rec.status_code == 200, rec.data
    assert rec.data["reconciled"] is True

    # Attendance changed after processing → reconciliation must flag drift.
    StaffAttendanceDay.objects.create(
        tenant_id=tenant_id, staff=teacher_staff, date=date(2026, 5, 5), status="absent"
    )
    rec2 = fin.get(f"/api/v1/payroll/runs/{run.data['id']}/reconcile/")
    assert rec2.data["reconciled"] is False
    assert rec2.data["out_of_sync"] == 1


@pytest.mark.django_db
def test_payroll_mark_paid_records_payment_history(client_for, tenant_id, teacher_staff):
    fin = client_for(["finance"], email="fin@cyed.edu.au")
    run = fin.post("/api/v1/payroll/runs/", {"period_label": "2026-06"}, format="json")
    # Cannot pay a run that was never processed.
    assert fin.post(f"/api/v1/payroll/runs/{run.data['id']}/mark-paid/").status_code == 400
    fin.post(f"/api/v1/payroll/runs/{run.data['id']}/process/")
    paid = fin.post(f"/api/v1/payroll/runs/{run.data['id']}/mark-paid/",
                    {"reference": "ABA-0001"}, format="json")
    assert paid.status_code == 200
    assert paid.data["payslips_paid"] == 1

    slips = fin.get(f"/api/v1/payroll/payslips/?payroll_run={run.data['id']}").data
    slips = slips["results"] if isinstance(slips, dict) else slips
    assert slips[0]["payment_status"] == "paid"
    assert slips[0]["payment_reference"] == "ABA-0001"


@pytest.mark.django_db
def test_payroll_is_finance_only(client_for, tenant_id, teacher_staff):
    teacher = client_for(["teacher"], email="ada@cyed.edu.au")
    assert teacher.get("/api/v1/payroll/runs/").status_code == 403
    assert teacher.get("/api/v1/payroll/payslips/").status_code == 403


# ══════════════════ HR workflows ══════════════════
@pytest.mark.django_db
def test_hr_onboard_offboard_lifecycle(client_for, tenant_id, teacher_staff):
    """HR manager: onboard, then offboard — contract ends, account deactivates."""
    hr = client_for(["tenant_admin"], email="hr@cyed.edu.au")
    on = hr.post(f"/api/v1/hr/staff/{teacher_staff.id}/onboard/")
    assert on.status_code == 200
    assert on.data["tasks_created"] == 7

    # Idempotent: re-running never duplicates the checklist.
    again = hr.post(f"/api/v1/hr/staff/{teacher_staff.id}/onboard/")
    assert again.data["tasks_created"] == 0
    assert len(again.data["tasks"]) == 7

    tasks = hr.get(f"/api/v1/hr/onboarding-tasks/?staff={teacher_staff.id}&open=1").data
    tasks = tasks["results"] if isinstance(tasks, dict) else tasks
    done = hr.post(f"/api/v1/hr/onboarding-tasks/{tasks[0]['id']}/complete/")
    assert done.status_code == 200 and done.data["is_completed"] is True
    assert hr.post(f"/api/v1/hr/onboarding-tasks/{tasks[0]['id']}/complete/").status_code == 400

    off = hr.post(f"/api/v1/hr/staff/{teacher_staff.id}/offboard/", {"end_date": "2026-06-30"},
                  format="json")
    assert off.status_code == 200
    assert off.data["is_active"] is False
    teacher_staff.refresh_from_db()
    assert teacher_staff.is_active is False
    assert not Contract.objects.filter(tenant_id=tenant_id, staff=teacher_staff, is_current=True).exists()


@pytest.mark.django_db
def test_offboarding_is_leadership_only(client_for, tenant_id, teacher_staff):
    teacher = client_for(["teacher"], email="ada@cyed.edu.au")
    assert teacher.post(f"/api/v1/hr/staff/{teacher_staff.id}/offboard/").status_code == 403


@pytest.mark.django_db
def test_leave_approval_writes_staff_attendance(client_for, tenant_id, teacher_staff):
    """HR manager approves leave → those days appear as paid leave, not absence."""
    from products.cyed.hr.compliance import ensure_entitlements

    # Approval now checks the balance, and a staff member with no entitlement
    # on record has an unknowable one — which is refused rather than assumed
    # sufficient. Open their leave year first, as a school would.
    ensure_entitlements(teacher_staff, 2026)

    hr = client_for(["tenant_admin"], email="hr@cyed.edu.au")
    leave = hr.post("/api/v1/hr/leave/", {
        "staff": str(teacher_staff.id), "leave_type": "annual",
        "start_date": "2026-04-06", "end_date": "2026-04-08", "days": "3",
    }, format="json")
    assert leave.status_code == 201, leave.data

    ok = hr.post(f"/api/v1/hr/leave/{leave.data['id']}/approve/")
    assert ok.status_code == 200 and ok.data["status"] == "approved"

    days = StaffAttendanceDay.objects.filter(
        tenant_id=tenant_id, staff=teacher_staff, date__gte=date(2026, 4, 6), date__lte=date(2026, 4, 8)
    )
    assert days.count() == 3
    assert all(d.status == "leave" and d.is_paid for d in days)

    # Deciding twice is rejected.
    assert hr.post(f"/api/v1/hr/leave/{leave.data['id']}/approve/").status_code == 400


@pytest.mark.django_db
def test_performance_review_confidentiality_and_flow(client_for, tenant_id, teacher_staff):
    head = client_for(["principal"], email="head@cyed.edu.au")
    rev = head.post("/api/v1/hr/performance-reviews/", {
        "staff": str(teacher_staff.id), "review_period": "2026 S1",
        "strengths": "Strong differentiation", "overall_rating": 4,
    }, format="json")
    assert rev.status_code == 201, rev.data

    # A teacher cannot author a review.
    ada = client_for(["teacher"], email="ada@cyed.edu.au")
    denied = ada.post("/api/v1/hr/performance-reviews/", {
        "staff": str(teacher_staff.id), "review_period": "2026 S2", "overall_rating": 5,
    }, format="json")
    assert denied.status_code == 403

    # Another teacher cannot read someone else's review.
    bob = Staff.objects.create(tenant_id=tenant_id, first_name="Bob", last_name="B",
                               email="bob@cyed.edu.au", role="teacher")
    bob_client = client_for(["teacher"], email="bob@cyed.edu.au")
    rows = bob_client.get("/api/v1/hr/performance-reviews/").data
    rows = rows["results"] if isinstance(rows, dict) else rows
    assert len(rows) == 0

    head.post(f"/api/v1/hr/performance-reviews/{rev.data['id']}/submit/")
    # Only the reviewed staff member may acknowledge.
    assert bob_client.post(f"/api/v1/hr/performance-reviews/{rev.data['id']}/acknowledge/").status_code in (403, 404)
    ack = ada.post(f"/api/v1/hr/performance-reviews/{rev.data['id']}/acknowledge/",
                   {"staff_comment": "Agreed"}, format="json")
    assert ack.status_code == 200 and ack.data["status"] == "acknowledged"


# ══════════════════ Procurement → Inventory → Accounting ══════════════════
@pytest.mark.django_db
def test_purchase_request_two_level_approval_to_goods_receipt(client_for, tenant_id):
    """Procurement officer: PR → finance approval → leadership approval → PO →
    receive → stock in + GL posted."""
    from products.cyed.finance.models import JournalEntry
    from products.cyed.inventory.models import InventoryItem
    from products.cyed.procurement.models import Supplier

    sup = Supplier.objects.create(tenant_id=tenant_id, name="Tech Supplies Pty Ltd")
    item = InventoryItem.objects.create(tenant_id=tenant_id, name="Laptop", unit="each",
                                        on_hand=0, reorder_level=3, category="IT equipment")

    officer = client_for(["teacher"], email="officer@cyed.edu.au")
    pr = officer.post("/api/v1/procurement/requests/", {
        "department": "IT", "justification": "Replace end-of-life laptops",
        "suggested_supplier": str(sup.id),
    }, format="json")
    assert pr.status_code == 201, pr.data

    # High value (10 × 1200 = 12000) → needs a second approval.
    officer.post("/api/v1/procurement/request-lines/", {
        "request": pr.data["id"], "description": "Laptop", "quantity": "10",
        "estimated_unit_price": "1200", "inventory_item": str(item.id),
    }, format="json")

    submitted = officer.post(f"/api/v1/procurement/requests/{pr.data['id']}/submit/")
    assert submitted.status_code == 200, submitted.data
    assert submitted.data["needs_second_approval"] is True
    assert len(submitted.data["approvals"]) == 2

    # A requester cannot approve their own request.
    assert officer.post(f"/api/v1/procurement/requests/{pr.data['id']}/approve/",
                        {"level": 1}, format="json").status_code == 403

    fin = client_for(["finance"], email="fin@cyed.edu.au")
    l1 = fin.post(f"/api/v1/procurement/requests/{pr.data['id']}/approve/", {"level": 1}, format="json")
    assert l1.status_code == 200 and l1.data["status"] == "approved_l1"

    # Finance cannot give the level-2 (leadership) approval.
    assert fin.post(f"/api/v1/procurement/requests/{pr.data['id']}/approve/",
                    {"level": 2}, format="json").status_code == 403

    head = client_for(["principal"], email="head@cyed.edu.au")
    l2 = head.post(f"/api/v1/procurement/requests/{pr.data['id']}/approve/", {"level": 2}, format="json")
    assert l2.status_code == 200 and l2.data["status"] == "approved"

    po = head.post(f"/api/v1/procurement/requests/{pr.data['id']}/convert/", {}, format="json")
    assert po.status_code == 201, po.data
    assert po.data["status"] == "ordered"
    line_id = po.data["lines"][0]["id"]

    rec = head.post(f"/api/v1/procurement/purchase-orders/{po.data['id']}/receive/", {
        "lines": [{"purchase_order_line_id": line_id, "quantity": 10}], "delivery_note": "DN-77",
    }, format="json")
    assert rec.status_code == 200, rec.data
    assert rec.data["purchase_order"]["status"] == "received"

    item.refresh_from_db()
    assert item.on_hand == Decimal("10.00")  # Inventory updated
    assert JournalEntry.objects.filter(tenant_id=tenant_id, posted=True).count() == 1  # GL posted


@pytest.mark.django_db
def test_rejected_purchase_request_cannot_convert(client_for, tenant_id):
    from products.cyed.procurement.models import Supplier

    sup = Supplier.objects.create(tenant_id=tenant_id, name="Vendor")
    officer = client_for(["teacher"], email="officer@cyed.edu.au")
    pr = officer.post("/api/v1/procurement/requests/",
                      {"department": "Art", "suggested_supplier": str(sup.id)}, format="json")
    officer.post("/api/v1/procurement/request-lines/", {
        "request": pr.data["id"], "description": "Easels", "quantity": "2",
        "estimated_unit_price": "100",
    }, format="json")
    officer.post(f"/api/v1/procurement/requests/{pr.data['id']}/submit/")

    fin = client_for(["finance"], email="fin@cyed.edu.au")
    rej = fin.post(f"/api/v1/procurement/requests/{pr.data['id']}/reject/",
                   {"level": 1, "comment": "Out of budget"}, format="json")
    assert rej.status_code == 200 and rej.data["status"] == "rejected"

    conv = fin.post(f"/api/v1/procurement/requests/{pr.data['id']}/convert/", {}, format="json")
    assert conv.status_code == 400


@pytest.mark.django_db
def test_submitting_empty_request_is_rejected(client_for, tenant_id):
    officer = client_for(["teacher"], email="officer@cyed.edu.au")
    pr = officer.post("/api/v1/procurement/requests/", {"department": "PE"}, format="json")
    r = officer.post(f"/api/v1/procurement/requests/{pr.data['id']}/submit/")
    assert r.status_code == 400


@pytest.mark.django_db
def test_low_stock_alert(client_for, tenant_id):
    from products.cyed.inventory.models import InventoryItem

    InventoryItem.objects.create(tenant_id=tenant_id, name="Whiteboard markers", category="consumables",
                                 on_hand=2, reorder_level=10)
    InventoryItem.objects.create(tenant_id=tenant_id, name="Projector", category="IT equipment",
                                 on_hand=0, reorder_level=1)
    InventoryItem.objects.create(tenant_id=tenant_id, name="Desks", category="furniture",
                                 on_hand=50, reorder_level=10)

    staff = client_for(["teacher"], email="t@cyed.edu.au")
    low = staff.get("/api/v1/inventory/items/low-stock/")
    assert low.status_code == 200
    assert low.data["count"] == 2
    assert low.data["critical"] == 1  # projector is fully out

    cats = staff.get("/api/v1/inventory/items/by-category/")
    assert {r["category"] for r in cats.data["rows"]} == {"consumables", "IT equipment", "furniture"}


# ══════════════════ Accounting ══════════════════
@pytest.mark.django_db
def test_financial_statements_and_budget(client_for, tenant_id):
    """Accountant (ERP): post entries, then P&L, balance sheet, budget variance."""
    from products.cyed.finance.models import Account

    cash = Account.objects.create(tenant_id=tenant_id, code="1000", name="Cash", account_type="asset")
    fees = Account.objects.create(tenant_id=tenant_id, code="4000", name="Tuition Fees",
                                  account_type="income")
    wages = Account.objects.create(tenant_id=tenant_id, code="5000", name="Wages",
                                   account_type="expense")

    acct = client_for(["finance"], email="acct@cyed.edu.au")
    acct.post("/api/v1/finance/journal-entries/", {
        "date": "2026-03-01", "reference": "JE1", "narration": "Fee income",
        "lines": [{"account": str(cash.id), "debit": "10000", "credit": "0"},
                  {"account": str(fees.id), "debit": "0", "credit": "10000"}],
    }, format="json")
    acct.post("/api/v1/finance/journal-entries/", {
        "date": "2026-03-15", "reference": "JE2", "narration": "Payroll",
        "lines": [{"account": str(wages.id), "debit": "6000", "credit": "0"},
                  {"account": str(cash.id), "debit": "0", "credit": "6000"}],
    }, format="json")

    # Unbalanced entries are rejected.
    bad = acct.post("/api/v1/finance/journal-entries/", {
        "date": "2026-03-16", "reference": "JE3",
        "lines": [{"account": str(cash.id), "debit": "50", "credit": "0"}],
    }, format="json")
    assert bad.status_code == 400

    pl = acct.get("/api/v1/finance/profit-and-loss/?from=2026-01-01&to=2026-12-31")
    assert pl.status_code == 200
    assert Decimal(pl.data["total_income"]) == Decimal("10000")
    assert Decimal(pl.data["total_expenses"]) == Decimal("6000")
    assert Decimal(pl.data["net_surplus"]) == Decimal("4000")

    bs = acct.get("/api/v1/finance/balance-sheet/?as_of=2026-12-31")
    assert bs.status_code == 200
    assert Decimal(bs.data["total_assets"]) == Decimal("4000")  # 10000 - 6000
    assert bs.data["balanced"] is True

    budget = acct.post("/api/v1/finance/budgets/", {
        "name": "Operating", "fiscal_year": "2026",
        "start_date": "2026-01-01", "end_date": "2026-12-31",
    }, format="json")
    assert budget.status_code == 201, budget.data
    acct.post("/api/v1/finance/budget-lines/", {
        "budget": budget.data["id"], "account": str(wages.id), "budgeted_amount": "8000",
    }, format="json")

    va = acct.get(f"/api/v1/finance/budgets/{budget.data['id']}/vs-actual/")
    row = va.data["rows"][0]
    assert Decimal(row["actual"]) == Decimal("6000")
    assert Decimal(row["variance"]) == Decimal("2000")  # under budget

    approved = acct.post(f"/api/v1/finance/budgets/{budget.data['id']}/approve/")
    assert approved.status_code == 200 and approved.data["status"] == "approved"


@pytest.mark.django_db
def test_bank_reconciliation(client_for, tenant_id):
    from products.cyed.finance.models import Account

    cash = Account.objects.create(tenant_id=tenant_id, code="1000", name="Cash", account_type="asset")
    fees = Account.objects.create(tenant_id=tenant_id, code="4000", name="Fees", account_type="income")
    acct = client_for(["finance"], email="acct@cyed.edu.au")
    je = acct.post("/api/v1/finance/journal-entries/", {
        "date": "2026-03-01", "reference": "JE1",
        "lines": [{"account": str(cash.id), "debit": "500", "credit": "0"},
                  {"account": str(fees.id), "debit": "0", "credit": "500"}],
    }, format="json")

    line = acct.post("/api/v1/finance/bank-lines/", {
        "date": "2026-03-01", "description": "Deposit", "amount": "500", "bank_reference": "BR1",
    }, format="json")
    assert line.status_code == 201, line.data

    summary = acct.get("/api/v1/finance/bank-lines/summary/").data
    assert summary["lines_outstanding"] == 1
    assert summary["fully_reconciled"] is False

    rec = acct.post(f"/api/v1/finance/bank-lines/{line.data['id']}/reconcile/",
                    {"entry": je.data["id"]}, format="json")
    assert rec.status_code == 200 and rec.data["is_reconciled"] is True

    # Reconciling twice is rejected.
    assert acct.post(f"/api/v1/finance/bank-lines/{line.data['id']}/reconcile/",
                     {"entry": je.data["id"]}, format="json").status_code == 400

    summary2 = acct.get("/api/v1/finance/bank-lines/summary/").data
    assert summary2["fully_reconciled"] is True


@pytest.mark.django_db
def test_accounting_is_finance_only(client_for, tenant_id):
    teacher = client_for(["teacher"], email="t@cyed.edu.au")
    assert teacher.get("/api/v1/finance/profit-and-loss/").status_code == 403
    assert teacher.get("/api/v1/finance/balance-sheet/").status_code == 403
    assert teacher.get("/api/v1/finance/budgets/").status_code == 403


# ══════════════════ Document Sign ══════════════════
@pytest.mark.django_db
def test_document_signing_flow_with_audit_trail(client_for, tenant_id, teacher_staff):
    """HR sends a contract; the staff member signs; the trail records everything."""
    hr = client_for(["tenant_admin"], email="hr@cyed.edu.au")
    doc = hr.post("/api/v1/docsign/documents/", {
        "title": "2026 Employment Contract", "doc_type": "staff_contract",
        "body": "Full-time teaching contract for 2026.", "staff": str(teacher_staff.id),
    }, format="json")
    assert doc.status_code == 201, doc.data
    doc_id = doc.data["id"]

    # Cannot send with no signatories.
    assert hr.post(f"/api/v1/docsign/documents/{doc_id}/send/").status_code == 400

    sig = hr.post(f"/api/v1/docsign/documents/{doc_id}/signatories/", {
        "name": "Ada Lovelace", "email": "ada@cyed.edu.au", "role": "staff", "order": 1,
    }, format="json")
    assert sig.status_code == 201, sig.data

    sent = hr.post(f"/api/v1/docsign/documents/{doc_id}/send/")
    assert sent.status_code == 200
    assert sent.data["status"] == "sent"
    assert sent.data["content_hash"]  # sealed

    # A non-signatory cannot sign.
    bob = client_for(["teacher"], email="bob@cyed.edu.au")
    assert bob.post(f"/api/v1/docsign/documents/{doc_id}/sign/",
                    {"typed_signature": "Bob"}, format="json").status_code in (403, 404)

    ada = client_for(["teacher"], email="ada@cyed.edu.au")
    # A typed name is required.
    assert ada.post(f"/api/v1/docsign/documents/{doc_id}/sign/", {}, format="json").status_code == 400

    signed = ada.post(f"/api/v1/docsign/documents/{doc_id}/sign/",
                      {"typed_signature": "Ada Lovelace"}, format="json")
    assert signed.status_code == 200, signed.data
    assert signed.data["status"] == "completed"

    # Signing twice is rejected.
    assert ada.post(f"/api/v1/docsign/documents/{doc_id}/sign/",
                    {"typed_signature": "Ada Lovelace"}, format="json").status_code == 400

    audit = hr.get(f"/api/v1/docsign/documents/{doc_id}/audit/")
    assert audit.status_code == 200
    actions = [e["action"] for e in audit.data["events"]]
    assert actions == ["created", "sent", "signed"]
    assert audit.data["verified"] is True
    assert audit.data["events"][-1]["actor"] == "ada@cyed.edu.au"


@pytest.mark.django_db
def test_tampering_after_send_is_detected(client_for, tenant_id):
    from products.cyed.docsign.models import SignableDocument

    hr = client_for(["tenant_admin"], email="hr@cyed.edu.au")
    doc = hr.post("/api/v1/docsign/documents/", {
        "title": "Excursion Permission", "doc_type": "permission_slip", "body": "Zoo trip, $20.",
    }, format="json")
    hr.post(f"/api/v1/docsign/documents/{doc.data['id']}/signatories/", {
        "name": "Parent", "email": "parent@home.com", "role": "parent",
    }, format="json")
    hr.post(f"/api/v1/docsign/documents/{doc.data['id']}/send/")

    # Alter the body after sealing — the hash no longer matches.
    obj = SignableDocument.objects.get(id=doc.data["id"])
    obj.body = "Zoo trip, $200."
    obj.save()
    assert obj.verify() is False

    parent = client_for(["parent"], email="parent@home.com")
    blocked = parent.post(f"/api/v1/docsign/documents/{doc.data['id']}/sign/",
                          {"typed_signature": "Parent"}, format="json")
    assert blocked.status_code == 409  # signing is blocked on a tampered document


@pytest.mark.django_db
def test_parent_only_sees_own_documents(client_for, tenant_id):
    hr = client_for(["tenant_admin"], email="hr@cyed.edu.au")
    mine = hr.post("/api/v1/docsign/documents/",
                   {"title": "Consent A", "doc_type": "consent_form", "body": "x"}, format="json")
    hr.post(f"/api/v1/docsign/documents/{mine.data['id']}/signatories/",
            {"name": "P1", "email": "p1@home.com", "role": "parent"}, format="json")
    other = hr.post("/api/v1/docsign/documents/",
                    {"title": "Consent B", "doc_type": "consent_form", "body": "y"}, format="json")
    hr.post(f"/api/v1/docsign/documents/{other.data['id']}/signatories/",
            {"name": "P2", "email": "p2@home.com", "role": "parent"}, format="json")

    p1 = client_for(["parent"], email="p1@home.com")
    rows = p1.get("/api/v1/docsign/documents/").data
    rows = rows["results"] if isinstance(rows, dict) else rows
    assert len(rows) == 1
    assert rows[0]["title"] == "Consent A"

    # Parents cannot author documents.
    assert p1.post("/api/v1/docsign/documents/",
                   {"title": "Fake", "body": "z"}, format="json").status_code == 403
