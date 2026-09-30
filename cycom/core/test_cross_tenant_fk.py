"""
Writable foreign keys are tenant-scoped on every TenantScopedModelViewSet:
another tenant's account / partner / product id -- top-level or inside
nested lines -- is rejected like a non-existent id, and nothing is created.
"""
import uuid
from datetime import date

import pytest
from rest_framework.test import APIClient

from products.cycom.accounting.models import Account
from products.cycom.ar_ap.models import Invoice, Partner
from products.cycom.inventory.models import Product, Warehouse
from products.cycom.procurement.models import PurchaseOrder

pytestmark = pytest.mark.django_db


@pytest.fixture
def client(mint_token, mock_jwks, tenant_id):
    token = mint_token({"sub": str(uuid.uuid4()), "tenant_id": str(tenant_id),
                        "realm_access": {"roles": ["tenant_admin"]}})
    c = APIClient()
    c.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return c


def _books(tid):
    return {
        "ar": Account.objects.create(tenant_id=tid, code="1100", name="AR", account_type="asset"),
        "rev": Account.objects.create(tenant_id=tid, code="4000", name="Rev", account_type="income"),
        "partner": Partner.objects.create(tenant_id=tid, name="P", partner_type="both"),
        "wh": Warehouse.objects.create(tenant_id=tid, code="WH", name="Main"),
        "product": Product.objects.create(tenant_id=tid, internal_ref="X", name="Thing"),
    }


def _invoice(b, line_account):
    return {"invoice_type": "customer", "partner": str(b["partner"].id), "date": "2026-09-01",
            "due_date": "2026-09-30", "currency": "JOD", "control_account": str(b["ar"].id),
            "lines": [{"account": str(line_account.id), "description": "x", "quantity": "1", "unit_price": "10"}]}


def test_own_records_still_work(client, tenant_id):
    mine = _books(tenant_id)
    resp = client.post("/api/v1/ar-ap/invoices/", _invoice(mine, mine["rev"]), format="json")
    assert resp.status_code == 201, resp.content


def test_other_tenants_top_level_fk_is_rejected(client, tenant_id):
    mine, theirs = _books(tenant_id), _books(uuid.uuid4())
    payload = _invoice(mine, mine["rev"])
    payload["partner"] = str(theirs["partner"].id)
    resp = client.post("/api/v1/ar-ap/invoices/", payload, format="json")
    assert resp.status_code == 400
    assert not Invoice.objects.filter(tenant_id=tenant_id).exists()


def test_other_tenants_fk_inside_nested_lines_is_rejected(client, tenant_id):
    mine, theirs = _books(tenant_id), _books(uuid.uuid4())
    resp = client.post("/api/v1/ar-ap/invoices/", _invoice(mine, theirs["rev"]), format="json")
    assert resp.status_code == 400
    assert not Invoice.objects.filter(tenant_id=tenant_id).exists()


def test_purchase_order_with_foreign_warehouse_and_product_is_rejected(client, tenant_id):
    mine, theirs = _books(tenant_id), _books(uuid.uuid4())
    base = {"vendor": str(mine["partner"].id), "warehouse": str(mine["wh"].id),
            "lines": [{"product": str(mine["product"].id), "quantity": "1", "unit_cost": "1",
                       "offset_account": str(mine["ar"].id)}]}
    assert client.post("/api/v1/procurement/orders/", base, format="json").status_code == 201
    bad_wh = {**base, "warehouse": str(theirs["wh"].id)}
    assert client.post("/api/v1/procurement/orders/", bad_wh, format="json").status_code == 400
    bad_line = {**base, "lines": [{**base["lines"][0], "product": str(theirs["product"].id)}]}
    assert client.post("/api/v1/procurement/orders/", bad_line, format="json").status_code == 400
    assert PurchaseOrder.objects.filter(tenant_id=tenant_id).count() == 1


def test_update_cannot_repoint_to_another_tenants_record(client, tenant_id):
    mine, theirs = _books(tenant_id), _books(uuid.uuid4())
    inv = Invoice.objects.create(tenant_id=tenant_id, invoice_type="customer", number="I-1",
                                 partner=mine["partner"], date=date(2026, 9, 1), due_date=date(2026, 9, 30),
                                 control_account=mine["ar"])
    resp = client.patch(f"/api/v1/ar-ap/invoices/{inv.id}/", {"partner": str(theirs["partner"].id)}, format="json")
    assert resp.status_code == 400
    inv.refresh_from_db()
    assert inv.partner_id == mine["partner"].id
