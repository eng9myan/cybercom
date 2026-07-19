import uuid
from datetime import date
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from products.cycom.accounting.models import Account
from products.cycom.inventory.models import Product, StockItem, StockMove, Warehouse
from products.cycom.inventory.services import apply_stock_move
from products.cycom.manufacturing.models import BillOfMaterial, BOMComponent, ManufacturingOrder


@pytest.fixture
def platform_admin_client(mint_token, mock_jwks, tenant_id):
    token = mint_token(
        {
            "sub": str(uuid.uuid4()),
            "email": "admin@cybercom.io",
            "tenant_id": str(tenant_id),
            "realm_access": {"roles": ["platform_admin"]},
        }
    )
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


@pytest.fixture
def mrp_fixtures(db, tenant_id):
    inv_account = Account.objects.create(
        tenant_id=tenant_id, code="1200", name="Inventory", account_type="asset"
    )
    wip_account = Account.objects.create(
        tenant_id=tenant_id, code="1250", name="WIP Clearing", account_type="asset"
    )
    warehouse = Warehouse.objects.create(tenant_id=tenant_id, code="WH-MAIN", name="Main")

    screw = Product.objects.create(tenant_id=tenant_id, sku="SCREW", name="Screw", inventory_account=inv_account)
    panel = Product.objects.create(tenant_id=tenant_id, sku="PANEL", name="Panel", inventory_account=inv_account)
    widget = Product.objects.create(tenant_id=tenant_id, sku="WIDGET", name="Widget", inventory_account=inv_account)

    for product, qty, cost in [(screw, Decimal("100"), Decimal("0.50")), (panel, Decimal("20"), Decimal("10.00"))]:
        receipt = StockMove.objects.create(
            tenant_id=tenant_id, move_type="receipt", product=product, warehouse=warehouse,
            quantity=qty, unit_cost=cost, date=date.today(), offset_account=inv_account, status="draft",
        )
        apply_stock_move(receipt)

    bom = BillOfMaterial.objects.create(tenant_id=tenant_id, product=widget, name="Widget BoM", quantity=1)
    BOMComponent.objects.create(tenant_id=tenant_id, bom=bom, component=screw, quantity=4)
    BOMComponent.objects.create(tenant_id=tenant_id, bom=bom, component=panel, quantity=1)

    return {"bom": bom, "warehouse": warehouse, "wip_account": wip_account, "widget": widget, "screw": screw, "panel": panel}


@pytest.mark.django_db
def test_complete_manufacturing_order_consumes_and_produces(platform_admin_client, tenant_id, mrp_fixtures):
    mo = ManufacturingOrder.objects.create(
        tenant_id=tenant_id,
        bom=mrp_fixtures["bom"],
        quantity=Decimal("5"),
        warehouse=mrp_fixtures["warehouse"],
        wip_account=mrp_fixtures["wip_account"],
        scheduled_date=date.today(),
    )

    resp = platform_admin_client.post(f"/api/v1/manufacturing/orders/{mo.id}/complete/")
    assert resp.status_code == 200, resp.content
    assert resp.data["status"] == "done"

    screw_item = StockItem.objects.get(tenant_id=tenant_id, product=mrp_fixtures["screw"], warehouse=mrp_fixtures["warehouse"])
    assert screw_item.quantity_on_hand == Decimal("80")  # 100 - (4*5)

    panel_item = StockItem.objects.get(tenant_id=tenant_id, product=mrp_fixtures["panel"], warehouse=mrp_fixtures["warehouse"])
    assert panel_item.quantity_on_hand == Decimal("15")  # 20 - (1*5)

    widget_item = StockItem.objects.get(tenant_id=tenant_id, product=mrp_fixtures["widget"], warehouse=mrp_fixtures["warehouse"])
    assert widget_item.quantity_on_hand == Decimal("5")
    # 5 units cost: (4*0.50 + 1*10.00) * 5 = 60.00 total / 5 = 12.00 each
    assert widget_item.average_cost == Decimal("12.0000")


@pytest.mark.django_db
def test_cannot_complete_without_enough_stock(platform_admin_client, tenant_id, mrp_fixtures):
    mo = ManufacturingOrder.objects.create(
        tenant_id=tenant_id,
        bom=mrp_fixtures["bom"],
        quantity=Decimal("1000"),
        warehouse=mrp_fixtures["warehouse"],
        wip_account=mrp_fixtures["wip_account"],
        scheduled_date=date.today(),
    )
    resp = platform_admin_client.post(f"/api/v1/manufacturing/orders/{mo.id}/complete/")
    assert resp.status_code == 400
