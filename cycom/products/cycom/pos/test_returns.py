"""Phase 3 — POS returns/refunds: full + partial (line-level), value-based
approval (retailgroup's real pos_refund tiers), and the manager PIN/barcode
approval fallback for a cashier working the till without a manager login."""

import uuid
from decimal import Decimal

import pytest
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.test import APIClient

from platform.provisioning.models import ApprovalPolicy, ApprovalTier
from products.cycom.accounting.models import Account
from products.cycom.access.credentials import set_manager_pin, verify_manager_credential
from products.cycom.access.models import Role, RoleAssignment
from products.cycom.catalog.models import Product
from products.cycom.inventory.models import SerialUnit, StockItem, StockLot, StockMove, Warehouse
from products.cycom.inventory.services import apply_stock_move
from products.cycom.pos.models import POSOrder, POSOrderLine, POSSession, PosReturn
from products.cycom.pos.services import approve_return, checkout_order, submit_return


@pytest.fixture
def shop(db, tenant_id):
    inv_acct = Account.objects.create(tenant_id=tenant_id, code="1140", name="Inventory", account_type="asset")
    accounts = dict(
        cash=Account.objects.create(tenant_id=tenant_id, code="1000", name="Cash", account_type="asset"),
        revenue=Account.objects.create(tenant_id=tenant_id, code="4000", name="Revenue", account_type="income"),
        tax=Account.objects.create(tenant_id=tenant_id, code="2120", name="Output VAT", account_type="liability"),
        cogs=Account.objects.create(tenant_id=tenant_id, code="5000", name="COGS", account_type="expense"),
    )
    wh = Warehouse.objects.create(tenant_id=tenant_id, code="WH", name="Main")
    return {"a": accounts, "wh": wh, "inv_acct": inv_acct}


def _stock(tenant_id, product, shop, qty, cost, **extra):
    move = StockMove.objects.create(
        tenant_id=tenant_id, move_type="receipt", product=product, warehouse=shop["wh"],
        quantity=Decimal(qty), unit_cost=Decimal(cost), date="2026-01-01",
        offset_account=shop["a"]["cash"], status="draft", **extra,
    )
    apply_stock_move(move)


def _checkout(tenant_id, shop, product, qty, price, **line_extra):
    session = POSSession.objects.create(tenant_id=tenant_id, warehouse=shop["wh"])
    order = POSOrder.objects.create(
        tenant_id=tenant_id, session=session, order_number=f"POS-{uuid.uuid4().hex[:8]}",
        cash_account=shop["a"]["cash"], revenue_account=shop["a"]["revenue"],
        tax_account=shop["a"]["tax"], cogs_account=shop["a"]["cogs"], currency="JOD",
    )
    POSOrderLine.objects.create(
        tenant_id=tenant_id, order=order, product=product,
        quantity=Decimal(str(qty)), unit_price=Decimal(str(price)), tax_percent=Decimal("16"),
        **line_extra,
    )
    checkout_order(order)
    order.refresh_from_db()
    return order


def _retailgroup_pos_refund_policy(tenant_id):
    policy = ApprovalPolicy.objects.create(
        tenant_id=tenant_id, document_type="pos_refund", name="POS Refund Approval"
    )
    ApprovalTier.objects.create(
        tenant_id=tenant_id, policy=policy, sequence=1,
        threshold_min=0, threshold_max=100, approver_role="Branch Manager",
    )
    ApprovalTier.objects.create(
        tenant_id=tenant_id, policy=policy, sequence=2,
        threshold_min=100, threshold_max=None, approver_role="Retail Operations Manager",
    )
    return policy


def _client_with_role(mint_token, tenant_id, role, sub=None):
    sub = sub or str(uuid.uuid4())
    token = mint_token({
        "sub": sub, "email": f"{role}@cybercom.io".replace(" ", ""),
        "tenant_id": str(tenant_id), "realm_access": {"roles": [role]},
    })
    c = APIClient()
    c.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return c


# ── Full / partial refund math + GL + restock ───────────────────────────────
@pytest.mark.django_db
def test_full_refund_reverses_gl_and_restocks(tenant_id, shop):
    product = Product.objects.create(
        tenant_id=tenant_id, name="Mug", internal_ref="MUG-1", inventory_account=shop["inv_acct"],
    )
    _stock(tenant_id, product, shop, qty=50, cost="2.00")
    order = _checkout(tenant_id, shop, product, qty=3, price="10.00")
    assert order.amount_subtotal == Decimal("30.00")

    line = order.lines.first()
    ret = submit_return(order, [{"order_line_id": str(line.id), "quantity": "3", "restock": True}])
    assert ret.status == "pending_approval"
    assert ret.amount_subtotal == Decimal("30.00")

    approve_return(ret, approved_by_user_id="mgr-1", approval_method="self")
    ret.refresh_from_db()
    assert ret.status == "approved"
    assert ret.journal_entry is not None
    assert ret.journal_entry.status == "posted"

    item = StockItem.objects.get(tenant_id=tenant_id, product=product, warehouse=shop["wh"])
    assert item.quantity_on_hand == Decimal("50")  # 50 - 3 sold + 3 returned


@pytest.mark.django_db
def test_partial_line_refund_math(tenant_id, shop):
    product = Product.objects.create(
        tenant_id=tenant_id, name="Mug", internal_ref="MUG-2", inventory_account=shop["inv_acct"],
    )
    _stock(tenant_id, product, shop, qty=50, cost="2.00")
    order = _checkout(tenant_id, shop, product, qty=5, price="10.00")
    line = order.lines.first()

    ret = submit_return(order, [{"order_line_id": str(line.id), "quantity": "2"}])
    assert ret.amount_subtotal == Decimal("20.00")  # 2/5 of the 50.00 line subtotal
    assert ret.amount_tax == Decimal("3.20")  # 2/5 of the 8.00 line tax (16%)

    approve_return(ret, approved_by_user_id="mgr-1", approval_method="self")
    item = StockItem.objects.get(tenant_id=tenant_id, product=product, warehouse=shop["wh"])
    assert item.quantity_on_hand == Decimal("47")  # 50 - 5 + 2


@pytest.mark.django_db
def test_over_return_across_two_requests_is_rejected(tenant_id, shop):
    product = Product.objects.create(
        tenant_id=tenant_id, name="Mug", internal_ref="MUG-3", inventory_account=shop["inv_acct"],
    )
    _stock(tenant_id, product, shop, qty=50, cost="2.00")
    order = _checkout(tenant_id, shop, product, qty=5, price="10.00")
    line = order.lines.first()

    ret1 = submit_return(order, [{"order_line_id": str(line.id), "quantity": "3"}])
    approve_return(ret1, approved_by_user_id="mgr-1", approval_method="self")

    with pytest.raises(ValidationError):
        submit_return(order, [{"order_line_id": str(line.id), "quantity": "3"}])  # only 2 left


@pytest.mark.django_db
def test_restock_false_skips_stock_move_but_still_refunds(tenant_id, shop):
    product = Product.objects.create(
        tenant_id=tenant_id, name="Mug", internal_ref="MUG-4", inventory_account=shop["inv_acct"],
    )
    _stock(tenant_id, product, shop, qty=50, cost="2.00")
    order = _checkout(tenant_id, shop, product, qty=2, price="10.00")
    line = order.lines.first()

    ret = submit_return(order, [{"order_line_id": str(line.id), "quantity": "2", "restock": False}])
    approve_return(ret, approved_by_user_id="mgr-1", approval_method="self")

    item = StockItem.objects.get(tenant_id=tenant_id, product=product, warehouse=shop["wh"])
    assert item.quantity_on_hand == Decimal("48")  # 50 - 2 sold, never restocked
    assert ret.journal_entry is not None  # cash/revenue/tax still reversed


# ── Batch / serial restock correctness ──────────────────────────────────────
@pytest.mark.django_db
def test_batch_product_restocks_to_the_original_lot(tenant_id, shop):
    product = Product.objects.create(
        tenant_id=tenant_id, name="Amoxicillin", internal_ref="RX-1",
        tracking_mode="batch", inventory_account=shop["inv_acct"],
    )
    _stock(tenant_id, product, shop, qty=20, cost="0.50", lot_number="LOT-A", expiry_date="2027-01-01")
    order = _checkout(tenant_id, shop, product, qty=5, price="2.00")
    line = order.lines.first()
    assert line.lot_number_at_sale == "LOT-A"

    ret = submit_return(order, [{"order_line_id": str(line.id), "quantity": "5"}])
    approve_return(ret, approved_by_user_id="mgr-1", approval_method="self")

    lot = StockLot.objects.get(tenant_id=tenant_id, product=product, lot_number="LOT-A")
    assert lot.quantity_on_hand == Decimal("20")  # 20 - 5 + 5


@pytest.mark.django_db
def test_serial_product_return_flips_unit_back_to_in_stock(tenant_id, shop):
    product = Product.objects.create(
        tenant_id=tenant_id, name="Phone", internal_ref="PHN-1",
        tracking_mode="serial", inventory_account=shop["inv_acct"],
    )
    _stock(tenant_id, product, shop, qty=2, cost="200", serial_numbers=["SN-A", "SN-B"])
    order = _checkout(tenant_id, shop, product, qty=1, price="450", serial_numbers=["SN-A"])
    line = order.lines.first()

    ret = submit_return(order, [
        {"order_line_id": str(line.id), "quantity": "1", "serial_numbers": ["SN-A"]}
    ])
    approve_return(ret, approved_by_user_id="mgr-1", approval_method="self")

    unit = SerialUnit.objects.get(tenant_id=tenant_id, serial_number="SN-A")
    assert unit.status == "in_stock"
    assert unit.warehouse_id == shop["wh"].id


# ── Value-based approval (real retailgroup tiers) ───────────────────────────
@pytest.mark.django_db
def test_return_approve_endpoint_enforces_retailgroup_tiers(tenant_id, shop, mint_token, mock_jwks):
    _retailgroup_pos_refund_policy(tenant_id)
    product = Product.objects.create(
        tenant_id=tenant_id, name="Speaker", internal_ref="SPK-1", inventory_account=shop["inv_acct"],
    )
    _stock(tenant_id, product, shop, qty=10, cost="20.00")
    # 3 * 50 = 150 subtotal -> Retail Operations Manager band (>100)
    order = _checkout(tenant_id, shop, product, qty=3, price="50.00")
    line = order.lines.first()
    ret = submit_return(order, [{"order_line_id": str(line.id), "quantity": "3"}])

    branch_mgr = _client_with_role(mint_token, tenant_id, "Branch Manager")
    resp = branch_mgr.post(f"/api/v1/pos/returns/{ret.id}/approve/")
    assert resp.status_code == 403, resp.content

    ops_mgr = _client_with_role(mint_token, tenant_id, "Retail Operations Manager")
    resp = ops_mgr.post(f"/api/v1/pos/returns/{ret.id}/approve/")
    assert resp.status_code == 200, resp.content
    ret.refresh_from_db()
    assert ret.status == "approved"
    assert ret.approval_method == "self"


# ── Manager PIN / barcode fallback ──────────────────────────────────────────
@pytest.fixture
def branch_manager_with_pin(tenant_id):
    _retailgroup_pos_refund_policy(tenant_id)
    role = Role.objects.create(tenant_id=tenant_id, name="Branch Manager")
    assignment = RoleAssignment.objects.create(tenant_id=tenant_id, user_id="mgr-user-1", role=role)
    set_manager_pin(assignment, "4242")
    return assignment


@pytest.mark.django_db
def test_pin_verification_matches_role_for_the_amount_band(tenant_id, branch_manager_with_pin):
    manager_id = verify_manager_credential(tenant_id, "pos_refund", Decimal("50"), pin="4242")
    assert manager_id == "mgr-user-1"


@pytest.mark.django_db
def test_pin_verification_fails_for_wrong_pin(tenant_id, branch_manager_with_pin):
    assert verify_manager_credential(tenant_id, "pos_refund", Decimal("50"), pin="0000") is None


@pytest.mark.django_db
def test_pin_verification_fails_when_amount_needs_a_higher_role(tenant_id, branch_manager_with_pin):
    # 150 -> Retail Operations Manager band; this PIN only proves Branch Manager.
    assert verify_manager_credential(tenant_id, "pos_refund", Decimal("150"), pin="4242") is None


@pytest.mark.django_db
def test_pin_rate_limit_trips_after_repeated_failures(tenant_id, branch_manager_with_pin):
    for _ in range(5):
        verify_manager_credential(tenant_id, "pos_refund", Decimal("50"), pin="wrong")
    with pytest.raises(PermissionDenied):
        verify_manager_credential(tenant_id, "pos_refund", Decimal("50"), pin="4242")  # correct, but locked out


@pytest.mark.django_db
def test_cashier_approves_return_via_manager_pin_and_audit_records_the_manager(
    tenant_id, shop, mint_token, mock_jwks, branch_manager_with_pin
):
    product = Product.objects.create(
        tenant_id=tenant_id, name="Kettle", internal_ref="KTL-1", inventory_account=shop["inv_acct"],
    )
    _stock(tenant_id, product, shop, qty=10, cost="10.00")
    order = _checkout(tenant_id, shop, product, qty=1, price="40.00")  # -> Branch Manager band
    line = order.lines.first()
    ret = submit_return(order, [{"order_line_id": str(line.id), "quantity": "1"}])

    cashier = _client_with_role(mint_token, tenant_id, "Cashier")
    resp = cashier.post(f"/api/v1/pos/returns/{ret.id}/approve/", {"manager_pin": "4242"}, format="json")
    assert resp.status_code == 200, resp.content

    ret.refresh_from_db()
    assert ret.status == "approved"
    assert ret.approved_by_user_id == "mgr-user-1"
    assert ret.approval_method == "pin"


@pytest.mark.django_db
def test_cashier_without_role_or_valid_pin_is_denied(tenant_id, shop, mint_token, mock_jwks, branch_manager_with_pin):
    product = Product.objects.create(
        tenant_id=tenant_id, name="Kettle", internal_ref="KTL-2", inventory_account=shop["inv_acct"],
    )
    _stock(tenant_id, product, shop, qty=10, cost="10.00")
    order = _checkout(tenant_id, shop, product, qty=1, price="40.00")
    line = order.lines.first()
    ret = submit_return(order, [{"order_line_id": str(line.id), "quantity": "1"}])

    cashier = _client_with_role(mint_token, tenant_id, "Cashier")
    resp = cashier.post(f"/api/v1/pos/returns/{ret.id}/approve/", {"manager_pin": "0000"}, format="json")
    assert resp.status_code == 403
