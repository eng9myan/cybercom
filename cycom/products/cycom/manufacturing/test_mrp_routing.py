"""Real MRP: work centers, routings, work orders, capacity — Phase 1 of the
Odoo gap-closure program. Reuses the mrp_fixtures convention from
test_manufacturing.py (widget BoM: 4 screws + 1 panel)."""

import uuid
from datetime import date
from decimal import Decimal

import pytest
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIClient

from products.cycom.accounting.models import Account
from products.cycom.inventory.models import Product, StockMove, Warehouse
from products.cycom.inventory.services import apply_stock_move
from products.cycom.manufacturing.models import (
    BillOfMaterial,
    BOMComponent,
    ManufacturingOrder,
    Routing,
    RoutingOperation,
    WorkCenter,
    WorkOrder,
)
from products.cycom.manufacturing.services import (
    complete_manufacturing_order,
    finish_work_order,
    start_work_order,
    work_center_load,
)


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
def routed_mrp(db, tenant_id):
    inv_account = Account.objects.create(
        tenant_id=tenant_id, code="1200", name="Inventory", account_type="asset"
    )
    wip_account = Account.objects.create(
        tenant_id=tenant_id, code="1250", name="WIP Clearing", account_type="asset"
    )
    warehouse = Warehouse.objects.create(tenant_id=tenant_id, code="WH-MAIN", name="Main")

    screw = Product.objects.create(tenant_id=tenant_id, internal_ref="SCREW", name="Screw", inventory_account=inv_account)
    panel = Product.objects.create(tenant_id=tenant_id, internal_ref="PANEL", name="Panel", inventory_account=inv_account)
    widget = Product.objects.create(tenant_id=tenant_id, internal_ref="WIDGET", name="Widget", inventory_account=inv_account)

    for product, qty, cost in [(screw, Decimal("100"), Decimal("0.50")), (panel, Decimal("20"), Decimal("10.00"))]:
        receipt = StockMove.objects.create(
            tenant_id=tenant_id, move_type="receipt", product=product, warehouse=warehouse,
            quantity=qty, unit_cost=cost, date=date.today(), offset_account=inv_account, status="draft",
        )
        apply_stock_move(receipt)

    bom = BillOfMaterial.objects.create(tenant_id=tenant_id, product=widget, name="Widget BoM", quantity=1)
    BOMComponent.objects.create(tenant_id=tenant_id, bom=bom, component=screw, quantity=4)
    BOMComponent.objects.create(tenant_id=tenant_id, bom=bom, component=panel, quantity=1)

    cutting = WorkCenter.objects.create(
        tenant_id=tenant_id, code="WC-CUT", name="Cutting", capacity_per_day_hours=8
    )
    assembly = WorkCenter.objects.create(
        tenant_id=tenant_id, code="WC-ASM", name="Assembly", capacity_per_day_hours=8
    )
    routing = Routing.objects.create(tenant_id=tenant_id, product=widget, name="Widget Routing")
    op1 = RoutingOperation.objects.create(
        tenant_id=tenant_id, routing=routing, sequence=10, work_center=cutting,
        name="Cut panel", duration_minutes=30,
    )
    op2 = RoutingOperation.objects.create(
        tenant_id=tenant_id, routing=routing, sequence=20, work_center=assembly,
        name="Assemble", duration_minutes=45,
    )

    return {
        "bom": bom, "warehouse": warehouse, "wip_account": wip_account,
        "routing": routing, "op1": op1, "op2": op2,
        "cutting": cutting, "assembly": assembly,
    }


def _make_mo(tenant_id, routed_mrp, qty=Decimal("5")):
    return ManufacturingOrder.objects.create(
        tenant_id=tenant_id,
        bom=routed_mrp["bom"],
        quantity=qty,
        warehouse=routed_mrp["warehouse"],
        wip_account=routed_mrp["wip_account"],
        scheduled_date=date.today(),
    )


@pytest.mark.django_db
def test_mo_auto_resolves_routing_and_generates_work_orders(tenant_id, routed_mrp):
    mo = _make_mo(tenant_id, routed_mrp)
    assert mo.routing_id == routed_mrp["routing"].id
    wos = list(mo.work_orders.order_by("sequence"))
    assert len(wos) == 2
    assert wos[0].status == "ready"
    assert wos[1].status == "pending"
    assert wos[0].work_center_id == routed_mrp["cutting"].id
    assert wos[1].work_center_id == routed_mrp["assembly"].id


@pytest.mark.django_db
def test_mo_without_routing_generates_no_work_orders(tenant_id, routed_mrp):
    # Delete the routing so the product has none — old shell behavior.
    routed_mrp["routing"].delete()
    mo = _make_mo(tenant_id, routed_mrp)
    assert mo.routing_id is None
    assert mo.work_orders.count() == 0


@pytest.mark.django_db
def test_cannot_start_pending_work_order_out_of_sequence(tenant_id, routed_mrp):
    mo = _make_mo(tenant_id, routed_mrp)
    second = mo.work_orders.get(sequence=20)
    with pytest.raises(ValidationError):
        start_work_order(second)


@pytest.mark.django_db
def test_starting_first_work_order_moves_mo_to_in_progress(tenant_id, routed_mrp):
    mo = _make_mo(tenant_id, routed_mrp)
    first = mo.work_orders.get(sequence=10)
    start_work_order(first)
    mo.refresh_from_db()
    assert mo.status == "in_progress"
    first.refresh_from_db()
    assert first.status == "in_progress"
    assert first.started_at is not None


@pytest.mark.django_db
def test_finishing_work_order_readies_the_next(tenant_id, routed_mrp):
    mo = _make_mo(tenant_id, routed_mrp)
    first = mo.work_orders.get(sequence=10)
    second = mo.work_orders.get(sequence=20)
    start_work_order(first)
    finish_work_order(first)
    second.refresh_from_db()
    assert second.status == "ready"


@pytest.mark.django_db
def test_cannot_complete_mo_before_all_work_orders_done(tenant_id, routed_mrp):
    mo = _make_mo(tenant_id, routed_mrp)
    with pytest.raises(ValidationError):
        complete_manufacturing_order(mo)


@pytest.mark.django_db
def test_complete_mo_succeeds_once_all_work_orders_done(tenant_id, routed_mrp):
    mo = _make_mo(tenant_id, routed_mrp)
    for wo_id in mo.work_orders.order_by("sequence").values_list("id", flat=True):
        wo = WorkOrder.objects.get(pk=wo_id)
        start_work_order(wo)
        finish_work_order(wo)
    mo.refresh_from_db()
    complete_manufacturing_order(mo)
    mo.refresh_from_db()
    assert mo.status == "done"


@pytest.mark.django_db
def test_work_center_load_reports_utilization(tenant_id, routed_mrp):
    _make_mo(tenant_id, routed_mrp, qty=Decimal("1"))
    result = work_center_load(
        routed_mrp["cutting"], date_from=date.today(), date_to=date.today()
    )
    assert result["planned_minutes"] == 30
    assert result["capacity_minutes"] == 8 * 60
    assert result["overloaded"] is False


@pytest.mark.django_db
def test_work_center_load_flags_overload(tenant_id, routed_mrp):
    # 20 MOs x 30 min cutting each = 600 min, capacity is 480 min/day.
    for _ in range(20):
        _make_mo(tenant_id, routed_mrp, qty=Decimal("1"))
    result = work_center_load(
        routed_mrp["cutting"], date_from=date.today(), date_to=date.today()
    )
    assert result["planned_minutes"] == 600
    assert result["overloaded"] is True


@pytest.mark.django_db
def test_work_order_actual_duration(tenant_id, routed_mrp):
    mo = _make_mo(tenant_id, routed_mrp)
    first = mo.work_orders.get(sequence=10)
    assert first.actual_duration_minutes is None
    start_work_order(first)
    finish_work_order(first)
    first.refresh_from_db()
    assert first.actual_duration_minutes is not None
    assert first.actual_duration_minutes >= 0


@pytest.mark.django_db
def test_api_start_and_finish_work_order(platform_admin_client, tenant_id, routed_mrp):
    mo = _make_mo(tenant_id, routed_mrp)
    first = mo.work_orders.get(sequence=10)

    resp = platform_admin_client.post(f"/api/v1/manufacturing/work-orders/{first.id}/start/")
    assert resp.status_code == 200, resp.data
    assert resp.data["status"] == "in_progress"

    resp = platform_admin_client.post(f"/api/v1/manufacturing/work-orders/{first.id}/finish/")
    assert resp.status_code == 200, resp.data
    assert resp.data["status"] == "done"


@pytest.mark.django_db
def test_work_center_tenant_isolation(platform_admin_client):
    WorkCenter.objects.create(tenant_id=uuid.uuid4(), code="WC", name="Foreign WC")
    resp = platform_admin_client.get("/api/v1/manufacturing/work-centers/")
    rows = resp.data["results"] if isinstance(resp.data, dict) else resp.data
    assert all(r["name"] != "Foreign WC" for r in rows)
