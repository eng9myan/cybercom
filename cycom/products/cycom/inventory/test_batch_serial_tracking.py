"""Phase 2 retail verticals — batch/lot + expiry (Pharmacy Retail), serial
number tracking (Electronics). Weight-based pricing (Grocery / Sweets &
Bakery) needs no service-level test: it reuses the existing quantity *
unit_price math unchanged (see pos.test_weight_pricing for the POS-line
surface check)."""

from datetime import date, timedelta
from decimal import Decimal

import pytest
from rest_framework.exceptions import ValidationError

from products.cycom.accounting.models import Account
from products.cycom.catalog.models import Product
from products.cycom.inventory.models import SerialUnit, StockItem, StockLot, StockMove, Warehouse
from products.cycom.inventory.services import apply_stock_move


@pytest.fixture
def accounts(db, tenant_id):
    return {
        "inv": Account.objects.create(tenant_id=tenant_id, code="1400", name="Inventory", account_type="asset"),
        "grni": Account.objects.create(tenant_id=tenant_id, code="2115", name="GRNI", account_type="liability"),
        "cogs": Account.objects.create(tenant_id=tenant_id, code="5100", name="COGS", account_type="expense"),
    }


@pytest.fixture
def warehouse(db, tenant_id):
    return Warehouse.objects.create(tenant_id=tenant_id, code="WH1", name="Main")


def _receipt(tenant_id, product, warehouse, accounts, *, qty, cost, lot_number="", expiry=None, serials=None):
    move = StockMove.objects.create(
        tenant_id=tenant_id, move_type="receipt", product=product, warehouse=warehouse,
        quantity=Decimal(qty), unit_cost=Decimal(cost), date="2026-01-01",
        offset_account=accounts["grni"], lot_number=lot_number, expiry_date=expiry,
        serial_numbers=serials or [],
    )
    return apply_stock_move(move)


def _issue(tenant_id, product, warehouse, accounts, *, qty, lot_number="", serials=None, override_expired=False):
    move = StockMove.objects.create(
        tenant_id=tenant_id, move_type="issue", product=product, warehouse=warehouse,
        quantity=Decimal(qty), date="2026-02-01",
        offset_account=accounts["cogs"], lot_number=lot_number, serial_numbers=serials or [],
    )
    return apply_stock_move(move, override_expired=override_expired)


# ── Batch / lot + expiry ────────────────────────────────────────────────────
@pytest.fixture
def batch_product(db, tenant_id, accounts):
    return Product.objects.create(
        tenant_id=tenant_id, name="Amoxicillin 500mg", internal_ref="RX-AMX-500",
        tracking_mode="batch", inventory_account=accounts["inv"],
    )


@pytest.mark.django_db
def test_batch_receipt_creates_lot_and_updates_aggregate(tenant_id, batch_product, warehouse, accounts):
    _receipt(tenant_id, batch_product, warehouse, accounts, qty=100, cost="0.50",
             lot_number="LOT-A", expiry=date(2027, 1, 1))

    lot = StockLot.objects.get(tenant_id=tenant_id, product=batch_product, lot_number="LOT-A")
    assert lot.quantity_on_hand == Decimal("100")
    assert lot.average_cost == Decimal("0.50")

    item = StockItem.objects.get(tenant_id=tenant_id, product=batch_product, warehouse=warehouse)
    assert item.quantity_on_hand == Decimal("100")


@pytest.mark.django_db
def test_receipt_of_batch_product_requires_lot_number(tenant_id, batch_product, warehouse, accounts):
    with pytest.raises(ValidationError):
        _receipt(tenant_id, batch_product, warehouse, accounts, qty=10, cost="0.50")


@pytest.mark.django_db
def test_issue_without_lot_picks_fefo(tenant_id, batch_product, warehouse, accounts):
    _receipt(tenant_id, batch_product, warehouse, accounts, qty=50, cost="0.50",
             lot_number="LOT-LATER", expiry=date(2027, 6, 1))
    _receipt(tenant_id, batch_product, warehouse, accounts, qty=50, cost="0.60",
             lot_number="LOT-SOONER", expiry=date(2027, 1, 1))

    move = _issue(tenant_id, batch_product, warehouse, accounts, qty=30)
    assert move.lot.lot_number == "LOT-SOONER"

    sooner = StockLot.objects.get(tenant_id=tenant_id, lot_number="LOT-SOONER")
    later = StockLot.objects.get(tenant_id=tenant_id, lot_number="LOT-LATER")
    assert sooner.quantity_on_hand == Decimal("20")
    assert later.quantity_on_hand == Decimal("50")  # untouched


@pytest.mark.django_db
def test_issue_spans_multiple_lots_when_one_isnt_enough(tenant_id, batch_product, warehouse, accounts):
    _receipt(tenant_id, batch_product, warehouse, accounts, qty=10, cost="0.50",
             lot_number="LOT-1", expiry=date(2027, 1, 1))
    _receipt(tenant_id, batch_product, warehouse, accounts, qty=50, cost="0.50",
             lot_number="LOT-2", expiry=date(2027, 6, 1))

    _issue(tenant_id, batch_product, warehouse, accounts, qty=15)

    assert StockLot.objects.get(tenant_id=tenant_id, lot_number="LOT-1").quantity_on_hand == Decimal("0")
    assert StockLot.objects.get(tenant_id=tenant_id, lot_number="LOT-2").quantity_on_hand == Decimal("45")


@pytest.mark.django_db
def test_issue_blocks_expired_lot_without_override(tenant_id, batch_product, warehouse, accounts):
    _receipt(tenant_id, batch_product, warehouse, accounts, qty=20, cost="0.50",
             lot_number="LOT-EXPIRED", expiry=date.today() - timedelta(days=1))

    with pytest.raises(ValidationError):
        _issue(tenant_id, batch_product, warehouse, accounts, qty=5)


@pytest.mark.django_db
def test_issue_expired_lot_allowed_with_admin_override(tenant_id, batch_product, warehouse, accounts):
    _receipt(tenant_id, batch_product, warehouse, accounts, qty=20, cost="0.50",
             lot_number="LOT-EXPIRED", expiry=date.today() - timedelta(days=1))

    move = _issue(tenant_id, batch_product, warehouse, accounts, qty=5, override_expired=True)
    assert move.status == "done"
    assert StockLot.objects.get(tenant_id=tenant_id, lot_number="LOT-EXPIRED").quantity_on_hand == Decimal("15")


@pytest.mark.django_db
def test_issue_named_lot_with_insufficient_quantity_raises(tenant_id, batch_product, warehouse, accounts):
    _receipt(tenant_id, batch_product, warehouse, accounts, qty=5, cost="0.50",
             lot_number="LOT-SMALL", expiry=date(2027, 1, 1))

    with pytest.raises(ValidationError):
        _issue(tenant_id, batch_product, warehouse, accounts, qty=10, lot_number="LOT-SMALL")


# ── Serial number tracking ──────────────────────────────────────────────────
@pytest.fixture
def serial_product(db, tenant_id, accounts):
    return Product.objects.create(
        tenant_id=tenant_id, name="4K TV 55in", internal_ref="TV-55-4K",
        tracking_mode="serial", inventory_account=accounts["inv"],
    )


@pytest.mark.django_db
def test_serial_receipt_creates_units_in_stock(tenant_id, serial_product, warehouse, accounts):
    _receipt(tenant_id, serial_product, warehouse, accounts, qty=2, cost="300",
             serials=["SN-001", "SN-002"])

    units = SerialUnit.objects.filter(tenant_id=tenant_id, product=serial_product)
    assert units.count() == 2
    assert all(u.status == "in_stock" for u in units)
    assert StockItem.objects.get(tenant_id=tenant_id, product=serial_product, warehouse=warehouse).quantity_on_hand == Decimal("2")


@pytest.mark.django_db
def test_serial_receipt_count_must_match_quantity(tenant_id, serial_product, warehouse, accounts):
    with pytest.raises(ValidationError):
        _receipt(tenant_id, serial_product, warehouse, accounts, qty=2, cost="300", serials=["SN-001"])


@pytest.mark.django_db
def test_serial_receipt_rejects_duplicate_within_request(tenant_id, serial_product, warehouse, accounts):
    with pytest.raises(ValidationError):
        _receipt(tenant_id, serial_product, warehouse, accounts, qty=2, cost="300",
                 serials=["SN-001", "SN-001"])


@pytest.mark.django_db
def test_serial_receipt_rejects_preexisting_serial(tenant_id, serial_product, warehouse, accounts):
    _receipt(tenant_id, serial_product, warehouse, accounts, qty=1, cost="300", serials=["SN-001"])
    with pytest.raises(ValidationError):
        _receipt(tenant_id, serial_product, warehouse, accounts, qty=1, cost="300", serials=["SN-001"])


@pytest.mark.django_db
def test_serial_issue_flips_status_and_clears_warehouse(tenant_id, serial_product, warehouse, accounts):
    _receipt(tenant_id, serial_product, warehouse, accounts, qty=2, cost="300", serials=["SN-001", "SN-002"])

    _issue(tenant_id, serial_product, warehouse, accounts, qty=1, serials=["SN-001"])

    sold = SerialUnit.objects.get(tenant_id=tenant_id, serial_number="SN-001")
    assert sold.status == "issued"
    assert sold.warehouse is None
    still_in_stock = SerialUnit.objects.get(tenant_id=tenant_id, serial_number="SN-002")
    assert still_in_stock.status == "in_stock"


@pytest.mark.django_db
def test_serial_issue_rejects_unknown_or_already_issued_serial(tenant_id, serial_product, warehouse, accounts):
    _receipt(tenant_id, serial_product, warehouse, accounts, qty=1, cost="300", serials=["SN-001"])
    _issue(tenant_id, serial_product, warehouse, accounts, qty=1, serials=["SN-001"])

    with pytest.raises(ValidationError):
        _issue(tenant_id, serial_product, warehouse, accounts, qty=1, serials=["SN-001"])  # already issued

    with pytest.raises(ValidationError):
        _issue(tenant_id, serial_product, warehouse, accounts, qty=1, serials=["SN-GHOST"])
