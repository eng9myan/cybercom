import uuid
from datetime import date, timedelta
from decimal import Decimal

import pytest
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIClient

from products.cycom.accounting.models import Account
from products.cycom.inventory.models import Product, StockMove, Warehouse
from products.cycom.inventory.services import apply_stock_move
from products.cycom.rental.models import RentalOrder
from products.cycom.rental.services import (
    add_rental_line,
    cancel_order,
    confirm_order,
    pick_up_order,
    return_line,
)


@pytest.fixture
def admin_client(mint_token, mock_jwks, tenant_id):
    token = mint_token(
        {
            "sub": str(uuid.uuid4()),
            "email": "rentals@cybercom.io",
            "tenant_id": str(tenant_id),
            "realm_access": {"roles": ["platform_admin"]},
        }
    )
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


@pytest.fixture
def fleet(db, tenant_id):
    inv_account = Account.objects.create(
        tenant_id=tenant_id, code="1300", name="Rental Fleet", account_type="asset"
    )
    warehouse = Warehouse.objects.create(tenant_id=tenant_id, code="YARD", name="Equipment Yard")
    excavator = Product.objects.create(
        tenant_id=tenant_id, internal_ref="EXC-1", name="Excavator", inventory_account=inv_account
    )
    receipt = StockMove.objects.create(
        tenant_id=tenant_id, move_type="receipt", product=excavator, warehouse=warehouse,
        quantity=Decimal("2"), unit_cost=Decimal("50000"), date=date.today(),
        offset_account=inv_account, status="draft",
    )
    apply_stock_move(receipt)
    return {"warehouse": warehouse, "excavator": excavator}


@pytest.fixture
def order(db, tenant_id):
    return RentalOrder.objects.create(tenant_id=tenant_id, customer_name="Acme Construction")


@pytest.mark.django_db
def test_add_line_within_fleet_size(tenant_id, fleet, order):
    line = add_rental_line(
        order, product=fleet["excavator"], warehouse=fleet["warehouse"], quantity=2,
        start_date=date(2026, 10, 1), end_date=date(2026, 10, 5), daily_rate=Decimal("300"),
    )
    assert line.rental_days == 4
    assert line.subtotal == Decimal("2400.00")  # 300 * 2 * 4


@pytest.mark.django_db
def test_add_line_exceeding_fleet_size_rejected(tenant_id, fleet, order):
    with pytest.raises(ValidationError):
        add_rental_line(
            order, product=fleet["excavator"], warehouse=fleet["warehouse"], quantity=3,
            start_date=date(2026, 10, 1), end_date=date(2026, 10, 5), daily_rate=Decimal("300"),
        )


@pytest.mark.django_db
def test_overlapping_reservations_respect_fleet_size(tenant_id, fleet, order):
    add_rental_line(
        order, product=fleet["excavator"], warehouse=fleet["warehouse"], quantity=1,
        start_date=date(2026, 10, 1), end_date=date(2026, 10, 10), daily_rate=Decimal("300"),
    )
    confirm_order(order)

    other_order = RentalOrder.objects.create(tenant_id=tenant_id, customer_name="Other Co")
    # 1 unit still free (fleet of 2), overlapping window.
    line2 = add_rental_line(
        other_order, product=fleet["excavator"], warehouse=fleet["warehouse"], quantity=1,
        start_date=date(2026, 10, 5), end_date=date(2026, 10, 8), daily_rate=Decimal("300"),
    )
    assert line2 is not None
    confirm_order(other_order)  # only confirmed+ reservations hold inventory

    # Now both units are reserved for that window — a third request fails.
    third_order = RentalOrder.objects.create(tenant_id=tenant_id, customer_name="Third Co")
    with pytest.raises(ValidationError):
        add_rental_line(
            third_order, product=fleet["excavator"], warehouse=fleet["warehouse"], quantity=1,
            start_date=date(2026, 10, 6), end_date=date(2026, 10, 7), daily_rate=Decimal("300"),
        )


@pytest.mark.django_db
def test_non_overlapping_dates_do_not_conflict(tenant_id, fleet, order):
    add_rental_line(
        order, product=fleet["excavator"], warehouse=fleet["warehouse"], quantity=2,
        start_date=date(2026, 10, 1), end_date=date(2026, 10, 5), daily_rate=Decimal("300"),
    )
    confirm_order(order)
    other_order = RentalOrder.objects.create(tenant_id=tenant_id, customer_name="Other Co")
    line = add_rental_line(
        other_order, product=fleet["excavator"], warehouse=fleet["warehouse"], quantity=2,
        start_date=date(2026, 10, 6), end_date=date(2026, 10, 10), daily_rate=Decimal("300"),
    )
    assert line is not None


@pytest.mark.django_db
def test_cancelled_order_frees_reservation(tenant_id, fleet, order):
    add_rental_line(
        order, product=fleet["excavator"], warehouse=fleet["warehouse"], quantity=2,
        start_date=date(2026, 10, 1), end_date=date(2026, 10, 5), daily_rate=Decimal("300"),
    )
    cancel_order(order)
    other_order = RentalOrder.objects.create(tenant_id=tenant_id, customer_name="Other Co")
    line = add_rental_line(
        other_order, product=fleet["excavator"], warehouse=fleet["warehouse"], quantity=2,
        start_date=date(2026, 10, 1), end_date=date(2026, 10, 5), daily_rate=Decimal("300"),
    )
    assert line is not None


@pytest.mark.django_db
def test_late_return_charges_late_fee(tenant_id, fleet, order):
    line = add_rental_line(
        order, product=fleet["excavator"], warehouse=fleet["warehouse"], quantity=1,
        start_date=date(2026, 10, 1), end_date=date(2026, 10, 5), daily_rate=Decimal("300"),
        late_fee_per_day=Decimal("100"),
    )
    confirm_order(order)
    pick_up_order(order)

    line = return_line(line, returned_date=date(2026, 10, 8))
    assert line.late_days == 3
    assert line.late_fee == Decimal("300.00")
    assert line.total == line.subtotal + Decimal("300.00")


@pytest.mark.django_db
def test_returning_all_lines_completes_order(tenant_id, fleet, order):
    line = add_rental_line(
        order, product=fleet["excavator"], warehouse=fleet["warehouse"], quantity=1,
        start_date=date(2026, 10, 1), end_date=date(2026, 10, 5), daily_rate=Decimal("300"),
    )
    confirm_order(order)
    pick_up_order(order)
    return_line(line)
    order.refresh_from_db()
    assert order.status == "returned"


@pytest.mark.django_db
def test_cannot_return_twice(tenant_id, fleet, order):
    line = add_rental_line(
        order, product=fleet["excavator"], warehouse=fleet["warehouse"], quantity=1,
        start_date=date(2026, 10, 1), end_date=date(2026, 10, 5), daily_rate=Decimal("300"),
    )
    confirm_order(order)
    pick_up_order(order)
    return_line(line)
    with pytest.raises(ValidationError):
        return_line(line)


@pytest.mark.django_db
def test_api_full_flow(admin_client, tenant_id, fleet, order):
    resp = admin_client.post(
        f"/api/v1/rental/orders/{order.id}/lines/",
        {
            "product": str(fleet["excavator"].id),
            "warehouse": str(fleet["warehouse"].id),
            "quantity": 1,
            "start_date": "2026-10-01",
            "end_date": "2026-10-05",
            "daily_rate": "300.00",
        },
        format="json",
    )
    assert resp.status_code == 201, resp.data
    line_id = resp.data["id"]

    resp = admin_client.post(f"/api/v1/rental/orders/{order.id}/confirm/")
    assert resp.status_code == 200
    resp = admin_client.post(f"/api/v1/rental/orders/{order.id}/pick-up/")
    assert resp.status_code == 200

    resp = admin_client.post(f"/api/v1/rental/lines/{line_id}/return/")
    assert resp.status_code == 200
    assert resp.data["returned_date"] is not None


@pytest.mark.django_db
def test_tenant_isolation(admin_client):
    RentalOrder.objects.create(tenant_id=uuid.uuid4(), customer_name="Foreign Customer")
    resp = admin_client.get("/api/v1/rental/orders/")
    rows = resp.data["results"] if isinstance(resp.data, dict) else resp.data
    assert all(r["customer_name"] != "Foreign Customer" for r in rows)
