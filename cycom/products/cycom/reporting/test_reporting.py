import uuid
from datetime import date
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from products.cycom.accounting.models import Account
from products.cycom.ar_ap.models import Invoice, Partner
from products.cycom.reporting.models import SavedReport
from products.cycom.sales.models import SalesOrder

pytestmark = pytest.mark.django_db


@pytest.fixture
def admin_client(mint_token, mock_jwks, tenant_id):
    token = mint_token(
        {
            "sub": str(uuid.uuid4()),
            "email": "analyst@cybercom.io",
            "tenant_id": str(tenant_id),
            "realm_access": {"roles": ["platform_admin"]},
        }
    )
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


@pytest.fixture
def sales_orders(tenant_id):
    SalesOrder.objects.create(
        tenant_id=tenant_id, number="SO-1", customer_name="Acme", order_date=date.today(),
        status="confirmed", amount_total=Decimal("1000"),
    )
    SalesOrder.objects.create(
        tenant_id=tenant_id, number="SO-2", customer_name="Acme", order_date=date.today(),
        status="confirmed", amount_total=Decimal("500"),
    )
    SalesOrder.objects.create(
        tenant_id=tenant_id, number="SO-3", customer_name="Beta Co", order_date=date.today(),
        status="draft", amount_total=Decimal("200"),
    )


@pytest.fixture
def invoice(tenant_id):
    ar = Account.objects.create(tenant_id=tenant_id, code="1100", name="AR", account_type="asset")
    partner = Partner.objects.create(tenant_id=tenant_id, name="Walk-in")
    return Invoice.objects.create(
        tenant_id=tenant_id, invoice_type="customer", number="INV-1", partner=partner,
        date=date.today(), due_date=date.today(), control_account=ar,
        status="posted", amount_total=Decimal("300"), amount_paid=Decimal("100"),
    )


def test_sources_meta_lists_whitelisted_sources(admin_client):
    resp = admin_client.get("/api/v1/reporting/sources/")
    assert resp.status_code == 200
    keys = [s["key"] for s in resp.data]
    assert "sales_orders" in keys
    assert "invoices" in keys
    sales = next(s for s in resp.data if s["key"] == "sales_orders")
    assert {"key": "status", "label": "Status"} in sales["dimensions"]
    assert {"key": "amount_total", "label": "Total Amount"} in sales["measures"]


def test_run_report_sums_measure_grouped_by_dimension(admin_client, tenant_id, sales_orders):
    report = SavedReport.objects.create(
        tenant_id=tenant_id, name="Sales by customer", source="sales_orders",
        dimension="customer", measure="amount_total", aggregation="sum",
    )
    resp = admin_client.get(f"/api/v1/reporting/saved-reports/{report.id}/run/")
    assert resp.status_code == 200
    rows = {r["label"]: r["value"] for r in resp.data}
    assert rows["Acme"] == 1500.0
    assert rows["Beta Co"] == 200.0


def test_run_report_count_measure(admin_client, tenant_id, sales_orders):
    report = SavedReport.objects.create(
        tenant_id=tenant_id, name="Order count by status", source="sales_orders",
        dimension="status", measure="count", aggregation="count",
    )
    resp = admin_client.get(f"/api/v1/reporting/saved-reports/{report.id}/run/")
    assert resp.status_code == 200
    rows = {r["label"]: r["value"] for r in resp.data}
    assert rows["confirmed"] == 2
    assert rows["draft"] == 1


def test_run_report_on_invoices_source(admin_client, tenant_id, invoice):
    report = SavedReport.objects.create(
        tenant_id=tenant_id, name="Paid vs total", source="invoices",
        dimension="status", measure="amount_paid", aggregation="sum",
    )
    resp = admin_client.get(f"/api/v1/reporting/saved-reports/{report.id}/run/")
    assert resp.status_code == 200
    assert resp.data == [{"label": "posted", "value": 100.0}]


def test_create_rejects_dimension_not_valid_for_source(admin_client):
    resp = admin_client.post(
        "/api/v1/reporting/saved-reports/",
        {"name": "Bad", "source": "sales_orders", "dimension": "not_a_real_field", "measure": "amount_total"},
        format="json",
    )
    assert resp.status_code == 400
    assert "dimension" in resp.data["detail"]


def test_create_rejects_unknown_source(admin_client):
    resp = admin_client.post(
        "/api/v1/reporting/saved-reports/",
        {"name": "Bad", "source": "not_a_real_model", "dimension": "status", "measure": "amount_total"},
        format="json",
    )
    assert resp.status_code == 400
    assert "source" in resp.data["detail"]


def test_tenant_isolation_on_report_run(admin_client, tenant_id, sales_orders):
    SalesOrder.objects.create(
        tenant_id=uuid.uuid4(), number="SO-FOREIGN", customer_name="Foreign Corp",
        order_date=date.today(), status="confirmed", amount_total=Decimal("99999"),
    )
    report = SavedReport.objects.create(
        tenant_id=tenant_id, name="Sales by customer", source="sales_orders",
        dimension="customer", measure="amount_total", aggregation="sum",
    )
    resp = admin_client.get(f"/api/v1/reporting/saved-reports/{report.id}/run/")
    labels = [r["label"] for r in resp.data]
    assert "Foreign Corp" not in labels


def test_admin_crud_requires_auth(tenant_id):
    resp = APIClient().get("/api/v1/reporting/saved-reports/")
    assert resp.status_code == 401
    resp = APIClient().get("/api/v1/reporting/sources/")
    assert resp.status_code == 401
