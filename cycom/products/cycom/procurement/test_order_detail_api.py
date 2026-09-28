"""
Purchase order detail API test.

The frontend PO detail page needs a real product name per line, not just
the FK id -- this mirrors the vendor_name field already on
PurchaseOrderSerializer (both read through the FK the same way).
"""

import uuid
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from products.cycom.accounting.models import Account
from products.cycom.ar_ap.models import Partner
from products.cycom.inventory.models import Product, Warehouse
from products.cycom.procurement.models import PurchaseOrder, PurchaseOrderLine

pytestmark = pytest.mark.django_db


@pytest.fixture
def admin_client(mint_token, mock_jwks, tenant_id):
    token = mint_token({
        "sub": str(uuid.uuid4()),
        "email": "ops@cybercom.io",
        "tenant_id": str(tenant_id),
        "realm_access": {"roles": ["tenant_admin"]},
    })
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


def test_purchase_order_line_includes_a_real_product_name(admin_client, tenant_id):
    grni = Account.objects.create(tenant_id=tenant_id, code="2115", name="GRNI", account_type="liability")
    wh = Warehouse.objects.create(tenant_id=tenant_id, code="WH-MAIN", name="Main")
    vendor = Partner.objects.create(tenant_id=tenant_id, name="Steel Supplier", partner_type="vendor")
    product = Product.objects.create(tenant_id=tenant_id, internal_ref="RB-12", name="Rebar 12mm")
    po = PurchaseOrder.objects.create(tenant_id=tenant_id, vendor=vendor, warehouse=wh, status="approved")
    PurchaseOrderLine.objects.create(
        tenant_id=tenant_id, order=po, product=product,
        quantity=Decimal("100"), unit_cost=Decimal("5"), offset_account=grni,
    )

    resp = admin_client.get(f"/api/v1/procurement/orders/{po.pk}/")
    assert resp.status_code == 200
    assert resp.data["lines"][0]["product_name"] == "Rebar 12mm"
