"""
Warehouse layout tests.

The important property is that adding locations is *additive*: valuation
still keys on (product, warehouse), nothing is double-counted, and a
warehouse that has never modelled a location behaves exactly as before.
"""

import uuid
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from products.cycom.catalog.models import Product
from products.cycom.inventory.layout import build_layout
from products.cycom.inventory.models import StockItem, StorageLocation, Warehouse

pytestmark = pytest.mark.django_db


@pytest.fixture
def admin_client(mint_token, mock_jwks, tenant_id):
    token = mint_token({
        "sub": str(uuid.uuid4()),
        "email": "wh@cybercom.io",
        "tenant_id": str(tenant_id),
        "realm_access": {"roles": ["tenant_admin", "platform_admin"]},
    })
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


@pytest.fixture
def warehouse(tenant_id):
    return Warehouse.objects.create(tenant_id=tenant_id, code="WH1", name="Main")


def loc(tenant_id, warehouse, code, ltype, parent=None, capacity=None, order=0):
    return StorageLocation.objects.create(
        tenant_id=tenant_id, warehouse=warehouse, code=code, location_type=ltype,
        parent=parent, capacity=capacity, sort_order=order,
    )


def stock(tenant_id, warehouse, name, qty, cost, location=None):
    product = Product.objects.create(
        tenant_id=tenant_id, name=name, internal_ref=name, product_type="STORABLE",
    )
    return StockItem.objects.create(
        tenant_id=tenant_id, product=product, warehouse=warehouse,
        quantity_on_hand=Decimal(str(qty)), average_cost=Decimal(str(cost)),
        location=location,
    )


def _layout(tenant_id, warehouse):
    return build_layout(
        StorageLocation.objects.filter(tenant_id=tenant_id, warehouse=warehouse),
        StockItem.objects.filter(tenant_id=tenant_id, warehouse=warehouse),
    )


def test_stock_rolls_up_from_bins_to_zone(tenant_id, warehouse):
    zone = loc(tenant_id, warehouse, "Z1", "zone")
    aisle = loc(tenant_id, warehouse, "A1", "aisle", parent=zone)
    bin_a = loc(tenant_id, warehouse, "B1", "bin", parent=aisle)
    bin_b = loc(tenant_id, warehouse, "B2", "bin", parent=aisle)
    stock(tenant_id, warehouse, "widget", 10, 5, location=bin_a)
    stock(tenant_id, warehouse, "gadget", 4, 25, location=bin_b)

    tree = _layout(tenant_id, warehouse)["tree"]
    assert len(tree) == 1
    z = tree[0]
    assert z["total_quantity"] == 14
    assert z["total_value"] == 150.0     # 10*5 + 4*25
    assert z["children"][0]["total_quantity"] == 14
    assert z["direct_quantity"] == 0     # zone holds nothing directly


def test_parent_totals_do_not_double_count_direct_and_child_stock(tenant_id, warehouse):
    zone = loc(tenant_id, warehouse, "Z1", "zone")
    b = loc(tenant_id, warehouse, "B1", "bin", parent=zone)
    stock(tenant_id, warehouse, "loose", 3, 10, location=zone)   # sitting in the zone itself
    stock(tenant_id, warehouse, "binned", 2, 10, location=b)

    z = _layout(tenant_id, warehouse)["tree"][0]
    assert z["direct_quantity"] == 3
    assert z["total_quantity"] == 5      # 3 direct + 2 from the bin, counted once


def test_unlocated_stock_is_reported_separately_not_lost(tenant_id, warehouse):
    loc(tenant_id, warehouse, "Z1", "zone")
    stock(tenant_id, warehouse, "floating", 7, 2)   # no location

    result = _layout(tenant_id, warehouse)
    assert result["unassigned"]["quantity"] == 7
    assert result["unassigned"]["value"] == 14.0
    assert result["totals"]["quantity"] == 7        # totals still include it


def test_warehouse_with_no_locations_still_reports_all_its_stock(tenant_id, warehouse):
    """The additive guarantee: never modelling a layout must not hide stock."""
    stock(tenant_id, warehouse, "a", 5, 3)
    stock(tenant_id, warehouse, "b", 5, 1)

    result = _layout(tenant_id, warehouse)
    assert result["tree"] == []
    assert result["totals"]["quantity"] == 10
    assert result["totals"]["value"] == 20.0


def test_occupancy_is_none_when_capacity_is_unknown(tenant_id, warehouse):
    """Unknown capacity and empty are different things; colouring them the
    same on the map would be a lie."""
    no_cap = loc(tenant_id, warehouse, "B1", "bin")
    with_cap = loc(tenant_id, warehouse, "B2", "bin", capacity=Decimal("100"))
    stock(tenant_id, warehouse, "x", 25, 1, location=with_cap)

    nodes = {n["code"]: n for n in _layout(tenant_id, warehouse)["tree"]}
    assert nodes["B1"]["occupancy_percent"] is None
    assert nodes["B2"]["occupancy_percent"] == 25.0


def test_over_capacity_reports_above_100_rather_than_clamping_to_full(tenant_id, warehouse):
    b = loc(tenant_id, warehouse, "B1", "bin", capacity=Decimal("10"))
    stock(tenant_id, warehouse, "x", 15, 1, location=b)
    assert _layout(tenant_id, warehouse)["tree"][0]["occupancy_percent"] == 150.0


def test_children_are_returned_in_sort_order(tenant_id, warehouse):
    zone = loc(tenant_id, warehouse, "Z1", "zone")
    loc(tenant_id, warehouse, "A3", "aisle", parent=zone, order=3)
    loc(tenant_id, warehouse, "A1", "aisle", parent=zone, order=1)
    loc(tenant_id, warehouse, "A2", "aisle", parent=zone, order=2)

    codes = [c["code"] for c in _layout(tenant_id, warehouse)["tree"][0]["children"]]
    assert codes == ["A1", "A2", "A3"]


def test_location_path_reads_top_down(tenant_id, warehouse):
    zone = loc(tenant_id, warehouse, "Z1", "zone")
    aisle = loc(tenant_id, warehouse, "A1", "aisle", parent=zone)
    b = loc(tenant_id, warehouse, "B1", "bin", parent=aisle)
    assert b.path == "Z1 / A1 / B1"


# ── API ────────────────────────────────────────────────────────────────────

def test_layout_endpoint_returns_tree_and_totals(admin_client, tenant_id, warehouse):
    zone = loc(tenant_id, warehouse, "Z1", "zone")
    b = loc(tenant_id, warehouse, "B1", "bin", parent=zone)
    stock(tenant_id, warehouse, "widget", 6, 5, location=b)

    resp = admin_client.get(f"/api/v1/inventory/warehouses/{warehouse.pk}/layout/")
    assert resp.status_code == 200
    assert resp.data["warehouse"]["code"] == "WH1"
    assert resp.data["totals"]["bins"] == 1
    assert resp.data["tree"][0]["total_quantity"] == 6


def test_api_refuses_a_parent_in_a_different_warehouse(admin_client, tenant_id, warehouse):
    other = Warehouse.objects.create(tenant_id=tenant_id, code="WH2", name="Other")
    foreign_parent = loc(tenant_id, other, "ZX", "zone")

    resp = admin_client.post("/api/v1/inventory/storage-locations/", {
        "warehouse": str(warehouse.pk), "parent": str(foreign_parent.pk),
        "code": "A1", "location_type": "aisle",
    }, format="json")
    assert resp.status_code == 400
    assert "same warehouse" in str(resp.data)


def test_api_refuses_a_location_containing_itself(admin_client, tenant_id, warehouse):
    z = loc(tenant_id, warehouse, "Z1", "zone")
    resp = admin_client.patch(
        f"/api/v1/inventory/storage-locations/{z.pk}/", {"parent": str(z.pk)}, format="json",
    )
    assert resp.status_code == 400


def test_layout_is_tenant_isolated(admin_client, tenant_id):
    other_tenant = uuid.uuid4()
    theirs = Warehouse.objects.create(tenant_id=other_tenant, code="X", name="Theirs")
    resp = admin_client.get(f"/api/v1/inventory/warehouses/{theirs.pk}/layout/")
    assert resp.status_code == 404
