import uuid

import pytest
from rest_framework.test import APIClient

from products.cyed.sis.models import Guardian, Student
from products.cyed.transport import routing
from products.cyed.transport.models import Bus, BusRoute, RouteStop, TransportSubscription, TransportZone


@pytest.fixture
def client_for(mint_token, mock_jwks, tenant_id):
    def _make(roles, email="user@cyed.edu.au"):
        token = mint_token({"sub": str(uuid.uuid4()), "email": email, "tenant_id": str(tenant_id),
                            "realm_access": {"roles": roles}})
        c = APIClient()
        c.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        return c
    return _make


def test_optimize_order_nearest_neighbour():
    stops = [
        {"id": "a", "name": "A", "lat": -33.87, "lng": 151.21},   # Sydney CBD
        {"id": "c", "name": "C", "lat": -33.80, "lng": 151.28},   # far
        {"id": "b", "name": "B", "lat": -33.88, "lng": 151.22},   # near A
    ]
    ordered, total = routing.optimize_order(stops)
    assert [s["id"] for s in ordered][:2] == ["a", "b"]  # nearest first
    assert total > 0


@pytest.mark.django_db
def test_ping_and_live_with_eta(client_for, tenant_id):
    admin = client_for(["tenant_admin"])
    bus = Bus.objects.create(tenant_id=tenant_id, identifier="Bus #7", capacity=30)
    route = BusRoute.objects.create(tenant_id=tenant_id, name="R1", bus=bus)
    RouteStop.objects.create(tenant_id=tenant_id, route=route, sequence=1, name="Stop 1", lat=-33.88, lng=151.22)
    RouteStop.objects.create(tenant_id=tenant_id, route=route, sequence=2, name="Stop 2", lat=-33.90, lng=151.24)

    ping = admin.post("/api/v1/transport/locations/",
                      {"bus": str(bus.id), "lat": "-33.87", "lng": "151.21", "speed_kmh": "30"}, format="json")
    assert ping.status_code == 201, ping.data

    live = admin.get(f"/api/v1/transport/buses/{bus.id}/live/")
    assert live.status_code == 200
    assert str(live.data["location"]["bus"]) == str(bus.id)
    assert len(live.data["etas"]) == 2
    assert live.data["etas"][0]["eta_min"] >= 0


@pytest.mark.django_db
def test_live_is_parent_scoped(client_for, tenant_id):
    bus = Bus.objects.create(tenant_id=tenant_id, identifier="Bus #7", capacity=30)
    zone = TransportZone.objects.create(tenant_id=tenant_id, name="Z", base_fee=500)
    child = Student.objects.create(tenant_id=tenant_id, first_name="Ivy", last_name="Chen", year_level=8)
    g = Guardian.objects.create(tenant_id=tenant_id, first_name="Jia", last_name="Chen", email="parent@home.com")
    g.students.add(child)
    TransportSubscription.objects.create(tenant_id=tenant_id, student=child, zone=zone, assigned_bus=bus,
                                         trip_type="full_trip", fee_amount=500)

    my_parent = client_for(["parent"], email="parent@home.com")
    assert my_parent.get(f"/api/v1/transport/buses/{bus.id}/live/").status_code == 200

    other = client_for(["parent"], email="other@home.com")
    assert other.get(f"/api/v1/transport/buses/{bus.id}/live/").status_code == 403


@pytest.mark.django_db
def test_route_optimize_reorders(client_for, tenant_id):
    admin = client_for(["tenant_admin"])
    route = BusRoute.objects.create(tenant_id=tenant_id, name="R2")
    RouteStop.objects.create(tenant_id=tenant_id, route=route, sequence=1, name="Far", lat=-33.80, lng=151.28)
    RouteStop.objects.create(tenant_id=tenant_id, route=route, sequence=2, name="Near1", lat=-33.88, lng=151.22)
    RouteStop.objects.create(tenant_id=tenant_id, route=route, sequence=3, name="Near2", lat=-33.87, lng=151.21)

    resp = admin.post(f"/api/v1/transport/routes/{route.id}/optimize/")
    assert resp.status_code == 200
    assert float(resp.data["total_distance_km"]) > 0
