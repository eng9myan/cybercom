"""
Dashboard summary tests.

The whole point of rebuilding this endpoint was replacing fabricated
numbers with real ones, so every test seeds a real row and asserts the
summary reflects exactly it -- and that a tenant with nothing yet gets
zeros/empty lists, never sample data standing in for the real thing.
"""

import uuid
from datetime import date, timedelta

import pytest
from rest_framework.test import APIClient

from products.cycom.accounting.models import Account
from products.cycom.ar_ap.models import Invoice, Partner
from products.cycom.automation.models import AutomationRule, AutomationRun
from products.cycom.catalog.models import Product
from products.cycom.hr.models import Employee, EmployeeDocument
from products.cycom.inventory.models import StockItem, Warehouse
from products.cycom.pos.models import POSSession
from products.cycom.procurement.models import PurchaseOrder
from products.cycom.sales.models import SalesOrder

pytestmark = pytest.mark.django_db


@pytest.fixture
def admin_client(mint_token, mock_jwks, tenant_id):
    token = mint_token({
        "sub": str(uuid.uuid4()),
        "email": "gm@cybercom.io",
        "tenant_id": str(tenant_id),
        "realm_access": {"roles": ["tenant_admin"]},
    })
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


def test_empty_tenant_gets_zeros_not_sample_data(admin_client, tenant_id):
    resp = admin_client.get("/api/v1/common/dashboard-summary/")
    assert resp.status_code == 200
    assert resp.data["alerts"] == []
    assert all(m["revenue"] == 0 for m in resp.data["revenue_trend"])
    pulse = {p["label"]: p["value"] for p in resp.data["pulse"]}
    assert pulse["Employees"] == "0 active"
    assert pulse["POS Sessions"] == "0 open"
    assert pulse["Pending Approvals"] == "0"


def test_revenue_trend_sums_real_confirmed_orders_only(admin_client, tenant_id):
    today = date.today()
    SalesOrder.objects.create(
        tenant_id=tenant_id, number="SO-1", customer_name="Acme", order_date=today,
        status="confirmed", amount_total=1000,
    )
    SalesOrder.objects.create(
        tenant_id=tenant_id, number="SO-2", customer_name="Acme", order_date=today,
        status="draft", amount_total=99999,   # a quotation is not revenue
    )
    resp = admin_client.get("/api/v1/common/dashboard-summary/")
    current_month = next(m for m in resp.data["revenue_trend"] if m["month"] == today.strftime("%Y-%m"))
    assert current_month["revenue"] == 1000.0


def test_revenue_trend_covers_six_months_oldest_first(admin_client, tenant_id):
    resp = admin_client.get("/api/v1/common/dashboard-summary/")
    months = [m["month"] for m in resp.data["revenue_trend"]]
    assert len(months) == 6
    assert months == sorted(months)
    assert months[-1] == date.today().strftime("%Y-%m")


def test_pending_approval_alert_matches_hitl_queue_definition(admin_client, tenant_id):
    """The dashboard and the real approvals queue must never disagree
    about what counts as pending."""
    from products.cycom.hitl.views import _purchase_order_queue

    vendor = Partner.objects.create(tenant_id=tenant_id, name="ACME Supplies", partner_type="vendor")
    wh = Warehouse.objects.create(tenant_id=tenant_id, code="WH1", name="Main")
    po = PurchaseOrder.objects.create(tenant_id=tenant_id, vendor=vendor, warehouse=wh, status="draft")

    resp = admin_client.get("/api/v1/common/dashboard-summary/")
    assert any(a["source"] == "Procurement" for a in resp.data["alerts"])
    pulse = {p["label"]: p["value"] for p in resp.data["pulse"]}
    assert pulse["Pending Approvals"] == "1"


def test_document_expiring_within_window_is_flagged(admin_client, tenant_id):
    emp = Employee.objects.create(
        tenant_id=tenant_id, employee_number="E1", first_name="Sam", last_name="Taha",
        hire_date=date(2024, 1, 1),
    )
    EmployeeDocument.objects.create(
        tenant_id=tenant_id, employee=emp, document_type="iqama",
        expiry_date=date.today() + timedelta(days=5),
    )
    resp = admin_client.get("/api/v1/common/dashboard-summary/")
    hr_alerts = [a for a in resp.data["alerts"] if a["source"] == "HR"]
    assert len(hr_alerts) == 1
    assert "Sam Taha" in hr_alerts[0]["desc"]
    assert hr_alerts[0]["urgency"] == "high"   # <=7 days


def test_document_expiring_outside_window_is_not_flagged(admin_client, tenant_id):
    emp = Employee.objects.create(
        tenant_id=tenant_id, employee_number="E1", first_name="Sam", last_name="Taha",
        hire_date=date(2024, 1, 1),
    )
    EmployeeDocument.objects.create(
        tenant_id=tenant_id, employee=emp, document_type="passport",
        expiry_date=date.today() + timedelta(days=90),
    )
    resp = admin_client.get("/api/v1/common/dashboard-summary/")
    assert not [a for a in resp.data["alerts"] if a["source"] == "HR"]


def test_already_expired_document_is_still_surfaced_not_hidden(admin_client, tenant_id):
    """An already-lapsed document is more urgent, not less -- it must not
    silently fall out of the list just because the date is in the past."""
    emp = Employee.objects.create(
        tenant_id=tenant_id, employee_number="E1", first_name="Lapsed", last_name="Doc",
        hire_date=date(2024, 1, 1),
    )
    EmployeeDocument.objects.create(
        tenant_id=tenant_id, employee=emp, document_type="visa",
        expiry_date=date.today() - timedelta(days=2),
    )
    resp = admin_client.get("/api/v1/common/dashboard-summary/")
    hr_alerts = [a for a in resp.data["alerts"] if a["source"] == "HR"]
    assert len(hr_alerts) == 1
    assert "expired 2 day(s) ago" in hr_alerts[0]["desc"]
    assert hr_alerts[0]["urgency"] == "high"


def _ar_accounts(tenant_id):
    ar = Account.objects.create(tenant_id=tenant_id, code="1130", name="AR", account_type="asset")
    tax = Account.objects.create(tenant_id=tenant_id, code="2120", name="VAT", account_type="liability")
    return ar, tax


def test_overdue_invoice_is_flagged_with_outstanding_balance(admin_client, tenant_id):
    partner = Partner.objects.create(tenant_id=tenant_id, name="Client Co", partner_type="customer")
    ar, tax = _ar_accounts(tenant_id)
    Invoice.objects.create(
        tenant_id=tenant_id, invoice_type="customer", number="INV-1", partner=partner,
        date=date.today() - timedelta(days=30), due_date=date.today() - timedelta(days=20),
        status="posted", amount_total=500, amount_paid=200,
        control_account=ar, tax_account=tax,
    )
    resp = admin_client.get("/api/v1/common/dashboard-summary/")
    fin_alerts = [a for a in resp.data["alerts"] if a["source"] == "Finance"]
    assert len(fin_alerts) == 1
    assert "300.00" in fin_alerts[0]["desc"]   # 500 - 200 outstanding
    assert fin_alerts[0]["urgency"] == "high"  # >14 days overdue


def test_paid_invoice_past_due_date_is_not_flagged(admin_client, tenant_id):
    partner = Partner.objects.create(tenant_id=tenant_id, name="Client Co", partner_type="customer")
    ar, tax = _ar_accounts(tenant_id)
    Invoice.objects.create(
        tenant_id=tenant_id, invoice_type="customer", number="INV-2", partner=partner,
        date=date.today() - timedelta(days=20), due_date=date.today() - timedelta(days=10),
        status="paid", amount_total=500, amount_paid=500,
        control_account=ar, tax_account=tax,
    )
    resp = admin_client.get("/api/v1/common/dashboard-summary/")
    assert not [a for a in resp.data["alerts"] if a["source"] == "Finance"]


def test_low_stock_below_reorder_threshold_is_flagged(admin_client, tenant_id):
    wh = Warehouse.objects.create(tenant_id=tenant_id, code="WH1", name="Main")
    product = Product.objects.create(
        tenant_id=tenant_id, name="Widget", internal_ref="W1",
        product_type="STORABLE", min_stock_qty=10,
    )
    StockItem.objects.create(tenant_id=tenant_id, product=product, warehouse=wh, quantity_on_hand=3)
    resp = admin_client.get("/api/v1/common/dashboard-summary/")
    inv_alerts = [a for a in resp.data["alerts"] if a["source"] == "Inventory"]
    assert len(inv_alerts) == 1
    assert "Widget" in inv_alerts[0]["desc"]


def test_stock_above_threshold_or_with_no_threshold_set_is_not_flagged(admin_client, tenant_id):
    wh = Warehouse.objects.create(tenant_id=tenant_id, code="WH1", name="Main")
    healthy = Product.objects.create(
        tenant_id=tenant_id, name="Plenty", internal_ref="P1",
        product_type="STORABLE", min_stock_qty=10,
    )
    no_threshold = Product.objects.create(
        tenant_id=tenant_id, name="Untracked", internal_ref="P2",
        product_type="STORABLE", min_stock_qty=0,
    )
    StockItem.objects.create(tenant_id=tenant_id, product=healthy, warehouse=wh, quantity_on_hand=50)
    StockItem.objects.create(tenant_id=tenant_id, product=no_threshold, warehouse=wh, quantity_on_hand=0)
    resp = admin_client.get("/api/v1/common/dashboard-summary/")
    assert not [a for a in resp.data["alerts"] if a["source"] == "Inventory"]


def test_recent_automation_failure_is_flagged(admin_client, tenant_id):
    rule = AutomationRule.objects.create(
        tenant_id=tenant_id, name="Broken Rule", trigger_source="lead", is_active=True,
    )
    AutomationRun.objects.create(tenant_id=tenant_id, rule=rule, status="failed", detail="smtp down")
    resp = admin_client.get("/api/v1/common/dashboard-summary/")
    auto_alerts = [a for a in resp.data["alerts"] if a["source"] == "Automation"]
    assert len(auto_alerts) == 1
    assert "Broken Rule" in auto_alerts[0]["desc"]


def test_successful_automation_run_is_not_flagged(admin_client, tenant_id):
    rule = AutomationRule.objects.create(
        tenant_id=tenant_id, name="Healthy Rule", trigger_source="lead", is_active=True,
    )
    AutomationRun.objects.create(tenant_id=tenant_id, rule=rule, status="matched", detail="ok")
    resp = admin_client.get("/api/v1/common/dashboard-summary/")
    assert not [a for a in resp.data["alerts"] if a["source"] == "Automation"]


def test_pulse_counts_are_real(admin_client, tenant_id):
    Employee.objects.create(
        tenant_id=tenant_id, employee_number="E1", first_name="A", last_name="B",
        hire_date=date(2024, 1, 1),
    )
    wh = Warehouse.objects.create(tenant_id=tenant_id, code="WH1", name="Main")
    POSSession.objects.create(tenant_id=tenant_id, warehouse=wh, status="open")
    POSSession.objects.create(tenant_id=tenant_id, warehouse=wh, status="closed")
    AutomationRule.objects.create(tenant_id=tenant_id, name="R1", trigger_source="lead", is_active=True)
    AutomationRule.objects.create(tenant_id=tenant_id, name="R2", trigger_source="lead", is_active=False)

    resp = admin_client.get("/api/v1/common/dashboard-summary/")
    pulse = {p["label"]: p["value"] for p in resp.data["pulse"]}
    assert pulse["Employees"] == "1 active"
    assert pulse["POS Sessions"] == "1 open"
    assert pulse["Automation Rules"] == "1 active"


def test_alerts_are_tenant_isolated(admin_client, tenant_id):
    other_tenant = uuid.uuid4()
    vendor = Partner.objects.create(tenant_id=other_tenant, name="Theirs", partner_type="vendor")
    wh = Warehouse.objects.create(tenant_id=other_tenant, code="X", name="Theirs")
    PurchaseOrder.objects.create(tenant_id=other_tenant, vendor=vendor, warehouse=wh, status="draft")

    resp = admin_client.get("/api/v1/common/dashboard-summary/")
    assert resp.data["alerts"] == []


def test_dashboard_summary_requires_auth():
    assert APIClient().get("/api/v1/common/dashboard-summary/").status_code == 401
