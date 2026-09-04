"""
Money-path invariant tests for POS checkout (`checkout_order`).

Checkout is the launch product's highest-volume money path: it issues stock,
posts revenue + tax + cash to the GL, and must never leave the books unbalanced
or stock negative. See docs/blueprint/H_nfr_checklist.md Q8, and
docs/blueprint/LAUNCH_READINESS.md §5.
"""
from decimal import Decimal

import pytest

from products.cycom.accounting.models import Account, JournalLine
from products.cycom.inventory.models import Product, StockItem, StockMove, Warehouse
from products.cycom.inventory.services import apply_stock_move
from products.cycom.pos.models import POSOrder, POSOrderLine, POSSession
from products.cycom.pos.services import checkout_order
from rest_framework.exceptions import ValidationError

T = "11111111-1111-1111-1111-111111111111"


@pytest.fixture
def shop(db):
    inv_acct = Account.objects.create(tenant_id=T, code="1140", name="Inventory", account_type="asset")
    a = dict(
        cash=Account.objects.create(tenant_id=T, code="1000", name="Cash", account_type="asset"),
        revenue=Account.objects.create(tenant_id=T, code="4000", name="Revenue", account_type="income"),
        tax=Account.objects.create(tenant_id=T, code="2120", name="Output VAT", account_type="liability"),
        cogs=Account.objects.create(tenant_id=T, code="5000", name="COGS", account_type="expense"),
    )
    wh = Warehouse.objects.create(tenant_id=T, code="WH", name="Main")
    prod = Product.objects.create(
        tenant_id=T, name="Latte", sku="LATTE", inventory_account=inv_acct,
    )
    # stock the shelf: receive 100 @ cost 1.00
    rcpt = StockMove.objects.create(
        tenant_id=T, move_type="receipt", product=prod, warehouse=wh,
        quantity=Decimal("100"), unit_cost=Decimal("1.00"), date="2026-07-01",
        offset_account=a["cash"], status="draft",
    )
    apply_stock_move(rcpt)
    return {"a": a, "wh": wh, "prod": prod}


def _order(shop, *, qty, price, tax_pct, order_type="sale"):
    session = POSSession.objects.create(tenant_id=T, warehouse=shop["wh"])
    order = POSOrder.objects.create(
        tenant_id=T, session=session, order_number=f"POS-{qty}-{price}",
        cash_account=shop["a"]["cash"], revenue_account=shop["a"]["revenue"],
        tax_account=shop["a"]["tax"], cogs_account=shop["a"]["cogs"],
        order_type=order_type, currency="JOD",
    )
    POSOrderLine.objects.create(
        tenant_id=T, order=order, product=shop["prod"],
        quantity=Decimal(str(qty)), unit_price=Decimal(str(price)),
        tax_percent=Decimal(str(tax_pct)),
    )
    return order


@pytest.mark.django_db
def test_checkout_posts_a_balanced_entry_with_correct_accounts(shop):
    order = _order(shop, qty=3, price="2.50", tax_pct="16")
    checkout_order(order)
    order.refresh_from_db()

    assert order.status == "paid"
    # 3 x 2.50 = 7.50 subtotal, 16% = 1.20 tax, 8.70 total
    assert order.amount_subtotal == Decimal("7.50")
    assert order.amount_tax == Decimal("1.20")
    assert order.amount_total == Decimal("8.70")

    lines = JournalLine.objects.filter(entry=order.journal_entry)
    assert sum(l.debit for l in lines) == sum(l.credit for l in lines)
    by_acct = {l.account_id: (l.debit, l.credit) for l in lines}
    assert by_acct[shop["a"]["cash"].id][0] == Decimal("8.70")      # cash debit = total
    assert by_acct[shop["a"]["revenue"].id][1] == Decimal("7.50")   # revenue credit = subtotal
    assert by_acct[shop["a"]["tax"].id][1] == Decimal("1.20")       # tax credit = tax


@pytest.mark.django_db
def test_checkout_decrements_stock_by_line_quantity(shop):
    item = StockItem.objects.get(tenant_id=T, product=shop["prod"], warehouse=shop["wh"])
    assert item.quantity_on_hand == Decimal("100")

    checkout_order(_order(shop, qty=4, price="2.50", tax_pct="16"))

    item.refresh_from_db()
    assert item.quantity_on_hand == Decimal("96")


@pytest.mark.django_db
def test_order_tax_equals_sum_of_line_taxes(shop):
    session = POSSession.objects.create(tenant_id=T, warehouse=shop["wh"])
    order = POSOrder.objects.create(
        tenant_id=T, session=session, order_number="POS-MULTI",
        cash_account=shop["a"]["cash"], revenue_account=shop["a"]["revenue"],
        tax_account=shop["a"]["tax"], cogs_account=shop["a"]["cogs"], currency="JOD",
    )
    for qty, price, tax in [("1", "2.50", "16"), ("2", "3.00", "0"), ("1", "5.00", "16")]:
        POSOrderLine.objects.create(
            tenant_id=T, order=order, product=shop["prod"],
            quantity=Decimal(qty), unit_price=Decimal(price), tax_percent=Decimal(tax),
        )
    line_tax = sum((l.tax_amount for l in order.lines.all()), Decimal("0"))
    checkout_order(order)
    order.refresh_from_db()
    assert order.amount_tax == line_tax


@pytest.mark.django_db
def test_oversell_is_rejected_stock_never_negative(shop):
    order = _order(shop, qty=999, price="2.50", tax_pct="16")
    with pytest.raises(ValidationError):
        checkout_order(order)
    item = StockItem.objects.get(tenant_id=T, product=shop["prod"], warehouse=shop["wh"])
    assert item.quantity_on_hand == Decimal("100")   # untouched
    order.refresh_from_db()
    assert order.status == "draft"                     # not marked paid


@pytest.mark.django_db
def test_empty_order_and_double_checkout_are_rejected(shop):
    session = POSSession.objects.create(tenant_id=T, warehouse=shop["wh"])
    empty = POSOrder.objects.create(
        tenant_id=T, session=session, order_number="POS-EMPTY",
        cash_account=shop["a"]["cash"], revenue_account=shop["a"]["revenue"],
        tax_account=shop["a"]["tax"], cogs_account=shop["a"]["cogs"], currency="JOD",
    )
    with pytest.raises(ValidationError):
        checkout_order(empty)

    paid = _order(shop, qty=1, price="2.50", tax_pct="16")
    checkout_order(paid)
    with pytest.raises(ValidationError):
        checkout_order(paid)
