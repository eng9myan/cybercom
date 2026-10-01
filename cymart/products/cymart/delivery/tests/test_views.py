import uuid
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from products.cymart.delivery.models import AssignmentStatus, DeliveryZone, Driver
from products.cymart.delivery.services import DispatchService
from products.cymart.orders.models import MarketplaceOrder

AMMAN_LAT, AMMAN_LNG = "31.9539", "35.9106"


def _authed_client(mint_token, mock_jwks, user_id):
    client = APIClient()
    token = mint_token({"sub": str(user_id), "roles": ["customer"], "permissions": []})
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


@pytest.mark.django_db
class TestZoneCheckAPI:
    def test_reports_deliverable_inside_zone(self, mint_token, mock_jwks):
        DeliveryZone.objects.create(
            name="Amman", city="Amman", center_lat=Decimal(AMMAN_LAT),
            center_lng=Decimal(AMMAN_LNG), radius_km=Decimal("15"),
        )
        client = _authed_client(mint_token, mock_jwks, uuid.uuid4())
        resp = client.get(f"/api/v1/delivery/zones/check/?lat={AMMAN_LAT}&lng={AMMAN_LNG}")
        assert resp.status_code == 200
        assert resp.json()["deliverable"] is True

    def test_reports_not_deliverable_outside_zone(self, mint_token, mock_jwks):
        DeliveryZone.objects.create(
            name="Amman", city="Amman", center_lat=Decimal(AMMAN_LAT),
            center_lng=Decimal(AMMAN_LNG), radius_km=Decimal("5"),
        )
        client = _authed_client(mint_token, mock_jwks, uuid.uuid4())
        resp = client.get("/api/v1/delivery/zones/check/?lat=30.5&lng=35.5")
        assert resp.status_code == 200
        assert resp.json()["deliverable"] is False


@pytest.mark.django_db
class TestOrderTrackingAPI:
    def test_customer_can_track_own_order(self, mint_token, mock_jwks):
        owner = uuid.uuid4()
        order = MarketplaceOrder.objects.create(
            idempotency_key=str(uuid.uuid4()), tenant_id=uuid.uuid4(), store_id=uuid.uuid4(),
            customer_id=owner, subtotal=Decimal("20.00"), total_amount=Decimal("20.00"),
        )
        Driver.objects.create(
            name="D1", phone="+962700000000", current_lat=Decimal(AMMAN_LAT),
            current_lng=Decimal(AMMAN_LNG), is_online=True,
        )
        DispatchService().assign_nearest_driver(order, Decimal(AMMAN_LAT), Decimal(AMMAN_LNG))

        client = _authed_client(mint_token, mock_jwks, owner)
        resp = client.get(f"/api/v1/delivery/track/{order.id}/")
        assert resp.status_code == 200
        assert resp.json()["status"] == AssignmentStatus.ASSIGNED

    def test_stranger_cannot_track_someone_elses_order(self, mint_token, mock_jwks):
        owner = uuid.uuid4()
        stranger = uuid.uuid4()
        order = MarketplaceOrder.objects.create(
            idempotency_key=str(uuid.uuid4()), tenant_id=uuid.uuid4(), store_id=uuid.uuid4(),
            customer_id=owner, subtotal=Decimal("20.00"), total_amount=Decimal("20.00"),
        )
        client = _authed_client(mint_token, mock_jwks, stranger)
        resp = client.get(f"/api/v1/delivery/track/{order.id}/")
        assert resp.status_code == 404

    def test_requires_auth(self):
        resp = APIClient().get(f"/api/v1/delivery/track/{uuid.uuid4()}/")
        assert resp.status_code in (401, 403)


@pytest.mark.django_db
class TestAssignBatchAPI:
    def test_batches_food_and_grocery_order_onto_one_driver(self, mint_token, mock_jwks):
        Driver.objects.create(
            name="D1", phone="+962700000000", current_lat=Decimal(AMMAN_LAT),
            current_lng=Decimal(AMMAN_LNG), is_online=True,
        )
        customer_id = uuid.uuid4()
        food_order = MarketplaceOrder.objects.create(
            idempotency_key=str(uuid.uuid4()), tenant_id=uuid.uuid4(), store_id=uuid.uuid4(),
            customer_id=customer_id, subtotal=Decimal("6.00"), total_amount=Decimal("6.00"),
        )
        grocery_order = MarketplaceOrder.objects.create(
            idempotency_key=str(uuid.uuid4()), tenant_id=uuid.uuid4(), store_id=uuid.uuid4(),
            customer_id=customer_id, subtotal=Decimal("15.00"), total_amount=Decimal("15.00"),
        )
        client = _authed_client(mint_token, mock_jwks, customer_id)
        resp = client.post(
            "/api/v1/delivery/assign/batch/",
            {
                "legs": [
                    {"order_id": str(food_order.id), "store_lat": AMMAN_LAT, "store_lng": AMMAN_LNG},
                    {"order_id": str(grocery_order.id), "store_lat": AMMAN_LAT, "store_lng": AMMAN_LNG},
                ]
            },
            format="json",
        )
        assert resp.status_code == 201, resp.content
        body = resp.json()
        assert len(body["stops"]) == 2

    def test_no_driver_available_returns_409(self, mint_token, mock_jwks):
        customer_id = uuid.uuid4()
        order = MarketplaceOrder.objects.create(
            idempotency_key=str(uuid.uuid4()), tenant_id=uuid.uuid4(), store_id=uuid.uuid4(),
            customer_id=customer_id, subtotal=Decimal("6.00"), total_amount=Decimal("6.00"),
        )
        client = _authed_client(mint_token, mock_jwks, customer_id)
        resp = client.post(
            "/api/v1/delivery/assign/batch/",
            {"legs": [{"order_id": str(order.id), "store_lat": AMMAN_LAT, "store_lng": AMMAN_LNG}]},
            format="json",
        )
        assert resp.status_code == 409
