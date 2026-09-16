import uuid
from datetime import date
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from products.cyed.assets.models import Asset
from products.cyed.inventory.models import InventoryItem


@pytest.fixture
def admin(mint_token, mock_jwks, tenant_id):
    token = mint_token({"sub": str(uuid.uuid4()), "email": "a@cyed.edu.au", "tenant_id": str(tenant_id),
                        "realm_access": {"roles": ["tenant_admin"]}})
    c = APIClient()
    c.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return c


@pytest.mark.django_db
def test_stock_moves_adjust_on_hand(admin, tenant_id):
    item = InventoryItem.objects.create(tenant_id=tenant_id, name="A4 Paper", unit="ream",
                                        on_hand=0, reorder_level=5)
    admin.post("/api/v1/inventory/moves/", {"item": str(item.id), "move_type": "in", "quantity": "20"}, format="json")
    admin.post("/api/v1/inventory/moves/", {"item": str(item.id), "move_type": "out", "quantity": "8"}, format="json")
    item.refresh_from_db()
    assert item.on_hand == Decimal("12.00")

    reorder = admin.get("/api/v1/inventory/items/?reorder=1").data
    reorder = reorder["results"] if isinstance(reorder, dict) else reorder
    assert len(reorder) == 0  # 12 > 5, not below reorder level


@pytest.mark.django_db
def test_procurement_po_total_and_receive(admin, tenant_id):
    """Receiving goods must move real stock and post to the ledger, not just
    flip a status flag."""
    from products.cyed.procurement.models import Supplier

    sup = Supplier.objects.create(tenant_id=tenant_id, name="Officeworks")
    item = InventoryItem.objects.create(tenant_id=tenant_id, name="Chairs", unit="each",
                                        on_hand=0, reorder_level=2)
    po = admin.post("/api/v1/procurement/purchase-orders/",
                    {"supplier": str(sup.id), "reference": "PO1", "status": "ordered"}, format="json")
    assert po.status_code == 201, po.data

    # A draft order cannot be received against — the order must be placed first.
    draft = admin.post("/api/v1/procurement/purchase-orders/",
                       {"supplier": str(sup.id), "reference": "PO-draft"}, format="json")
    blocked = admin.post(f"/api/v1/procurement/purchase-orders/{draft.data['id']}/receive/",
                         {"lines": [{"purchase_order_line_id": "x", "quantity": 1}]}, format="json")
    assert blocked.status_code == 400
    line = admin.post("/api/v1/procurement/order-lines/",
                      {"purchase_order": po.data["id"], "description": "Chairs", "quantity": "10",
                       "unit_price": "45", "inventory_item": str(item.id)},
                      format="json")
    assert line.status_code == 201, line.data
    detail = admin.get(f"/api/v1/procurement/purchase-orders/{po.data['id']}/").data
    assert Decimal(detail["total"]) == Decimal("450.00")

    # Partial receipt: 4 of 10.
    part = admin.post(
        f"/api/v1/procurement/purchase-orders/{po.data['id']}/receive/",
        {"lines": [{"purchase_order_line_id": line.data["id"], "quantity": 4}], "delivery_note": "DN-1"},
        format="json",
    )
    assert part.status_code == 200, part.data
    assert part.data["purchase_order"]["status"] == "partially_received"
    item.refresh_from_db()
    assert item.on_hand == Decimal("4.00")  # stock actually moved

    # Over-receipt is rejected (only 6 outstanding).
    over = admin.post(
        f"/api/v1/procurement/purchase-orders/{po.data['id']}/receive/",
        {"lines": [{"purchase_order_line_id": line.data["id"], "quantity": 99}]}, format="json",
    )
    assert over.status_code == 400

    # Remaining 6 completes the order.
    rest = admin.post(
        f"/api/v1/procurement/purchase-orders/{po.data['id']}/receive/",
        {"lines": [{"purchase_order_line_id": line.data["id"], "quantity": 6}]}, format="json",
    )
    assert rest.data["purchase_order"]["status"] == "received"
    item.refresh_from_db()
    assert item.on_hand == Decimal("10.00")

    # The receipt posted a balanced Dr Inventory / Cr Accounts Payable entry.
    from products.cyed.finance.models import JournalEntry

    entries = JournalEntry.objects.filter(tenant_id=tenant_id, posted=True)
    assert entries.count() == 2  # one per receipt
    assert all(e.is_balanced for e in entries)


@pytest.mark.django_db
def test_asset_depreciation(admin, tenant_id):
    asset = Asset.objects.create(tenant_id=tenant_id, name="Laptop", acquisition_cost=Decimal("2000"),
                                 salvage_value=Decimal("200"), useful_life_years=4,
                                 acquisition_date=date.today())
    detail = admin.get(f"/api/v1/assets/assets/{asset.id}/").data
    assert Decimal(detail["annual_depreciation"]) == Decimal("450.00")  # (2000-200)/4
    assert Decimal(detail["current_book_value"]) == Decimal("2000.00")  # brand new
