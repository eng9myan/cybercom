"""Purchase-order print action (ported from cyshop — CyCom's procurement
API had no print/PDF path at all before this)."""

import uuid
from decimal import Decimal

import pytest
from django.test import TestCase
from rest_framework.test import APIClient

from products.cycom.accounting.models import Account
from products.cycom.ar_ap.models import Partner
from products.cycom.inventory.models import Product, Warehouse
from products.cycom.procurement.models import PurchaseOrder, PurchaseOrderLine
from products.cycom.procurement.printing import purchase_order_html

TENANT = uuid.uuid4()


class PurchaseOrderPrintTests(TestCase):
    def setUp(self):
        self.grni = Account.objects.create(
            tenant_id=TENANT, code="2115", name="GRNI", account_type="liability"
        )
        self.wh = Warehouse.objects.create(tenant_id=TENANT, code="WH-MAIN", name="Main")
        self.vendor = Partner.objects.create(
            tenant_id=TENANT, name="Steel Supplier", partner_type="vendor",
            email="sales@steelsupplier.example", phone="+962700000000",
        )
        self.product = Product.objects.create(
            tenant_id=TENANT, internal_ref="RB-12", name="Rebar 12mm"
        )
        self.po = PurchaseOrder.objects.create(
            tenant_id=TENANT, vendor=self.vendor, warehouse=self.wh, status="approved",
            currency="JOD",
        )
        PurchaseOrderLine.objects.create(
            tenant_id=TENANT, order=self.po, product=self.product,
            quantity=Decimal("100"), unit_cost=Decimal("5"), offset_account=self.grni,
        )

    def test_html_contains_vendor_and_line_totals(self):
        html = purchase_order_html(self.po)
        self.assertIn("Steel Supplier", html)
        self.assertIn("Rebar 12mm", html)
        self.assertIn("sales@steelsupplier.example", html)
        self.assertIn("500.00", html)  # 100 * 5
        self.assertIn(f"PO-{str(self.po.id)[:8].upper()}", html)

    def test_html_has_no_tenant_falls_back_gracefully(self):
        # No real Tenant row backs this UUID in these tests — must not crash.
        html = purchase_order_html(self.po)
        self.assertIn("<!doctype html>", html)


@pytest.mark.django_db
def test_print_action_returns_html(mint_token, mock_jwks):
    tenant_id = uuid.uuid4()
    grni = Account.objects.create(tenant_id=tenant_id, code="2115", name="GRNI", account_type="liability")
    wh = Warehouse.objects.create(tenant_id=tenant_id, code="WH-MAIN", name="Main")
    vendor = Partner.objects.create(tenant_id=tenant_id, name="Steel Supplier", partner_type="vendor")
    product = Product.objects.create(tenant_id=tenant_id, internal_ref="RB-12", name="Rebar 12mm")
    po = PurchaseOrder.objects.create(tenant_id=tenant_id, vendor=vendor, warehouse=wh, currency="JOD")
    PurchaseOrderLine.objects.create(
        tenant_id=tenant_id, order=po, product=product,
        quantity=Decimal("10"), unit_cost=Decimal("2"), offset_account=grni,
    )

    token = mint_token({
        "sub": str(uuid.uuid4()), "email": "gm@cybercom.io",
        "tenant_id": str(tenant_id), "realm_access": {"roles": ["general_manager"]},
    })
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    resp = client.get(f"/api/v1/procurement/orders/{po.id}/print/")
    assert resp.status_code == 200, resp.content
    assert resp["Content-Type"] == "text/html"
    assert b"Steel Supplier" in resp.content
