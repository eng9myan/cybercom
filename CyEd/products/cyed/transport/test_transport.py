import uuid
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from products.cyed.notifications.models import Notification
from products.cyed.sis.models import Guardian, Student
from products.cyed.transport.models import Bus, RfidBoardingEvent, TransportZone


@pytest.fixture
def client_for(mint_token, mock_jwks, tenant_id):
    def _make(roles, email="user@cyed.edu.au"):
        token = mint_token({"sub": str(uuid.uuid4()), "email": email, "tenant_id": str(tenant_id),
                            "realm_access": {"roles": roles}})
        c = APIClient()
        c.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        return c
    return _make


@pytest.mark.django_db
def test_fee_by_trip_type(client_for, tenant_id):
    admin = client_for(["tenant_admin"])
    zone = TransportZone.objects.create(tenant_id=tenant_id, name="Zone 2", min_km=5, max_km=10, base_fee=1000)
    student = Student.objects.create(tenant_id=tenant_id, first_name="Minh", last_name="Nguyen", year_level=8)

    full = admin.post("/api/v1/transport/subscriptions/",
                      {"student": str(student.id), "zone": str(zone.id), "trip_type": "full_trip"}, format="json")
    assert full.status_code == 201, full.data
    assert Decimal(full.data["fee_amount"]) == Decimal("1000.00")

    student2 = Student.objects.create(tenant_id=tenant_id, first_name="Ava", last_name="Lee", year_level=8)
    half = admin.post("/api/v1/transport/subscriptions/",
                      {"student": str(student2.id), "zone": str(zone.id), "trip_type": "half_morning"}, format="json")
    assert Decimal(half.data["fee_amount"]) == Decimal("600.00")


@pytest.mark.django_db
def test_bus_capacity_enforced(client_for, tenant_id):
    admin = client_for(["tenant_admin"])
    zone = TransportZone.objects.create(tenant_id=tenant_id, name="Z1", base_fee=500)
    bus = Bus.objects.create(tenant_id=tenant_id, identifier="Bus #1", capacity=1)
    s1 = Student.objects.create(tenant_id=tenant_id, first_name="A", last_name="One", year_level=8)
    s2 = Student.objects.create(tenant_id=tenant_id, first_name="B", last_name="Two", year_level=8)

    ok = admin.post("/api/v1/transport/subscriptions/",
                    {"student": str(s1.id), "zone": str(zone.id), "trip_type": "full_trip", "assigned_bus": str(bus.id)},
                    format="json")
    assert ok.status_code == 201, ok.data
    full = admin.post("/api/v1/transport/subscriptions/",
                      {"student": str(s2.id), "zone": str(zone.id), "trip_type": "full_trip", "assigned_bus": str(bus.id)},
                      format="json")
    assert full.status_code == 400  # bus at capacity


@pytest.mark.django_db
def test_rfid_boarding_notifies_guardian(tenant_id):
    from django.utils import timezone
    student = Student.objects.create(tenant_id=tenant_id, first_name="Minh", last_name="Nguyen", year_level=8)
    g = Guardian.objects.create(tenant_id=tenant_id, first_name="Jia", last_name="Nguyen", email="parent@home.com")
    g.students.add(student)
    bus = Bus.objects.create(tenant_id=tenant_id, identifier="Bus #12", capacity=30)

    RfidBoardingEvent.objects.create(tenant_id=tenant_id, student=student, bus=bus, event_type="board",
                                     occurred_at=timezone.now())
    notes = Notification.objects.filter(tenant_id=tenant_id, related_model="cyed_transport.RfidBoardingEvent")
    assert notes.count() == 1
    assert "boarded Bus #12" in notes.first().body


@pytest.mark.django_db
def test_subscription_scoped_to_parent(client_for, tenant_id):
    admin = client_for(["tenant_admin"])
    zone = TransportZone.objects.create(tenant_id=tenant_id, name="Z1", base_fee=500)
    mine = Student.objects.create(tenant_id=tenant_id, first_name="Ivy", last_name="Chen", year_level=8)
    other = Student.objects.create(tenant_id=tenant_id, first_name="Sam", last_name="Other", year_level=8)
    g = Guardian.objects.create(tenant_id=tenant_id, first_name="Jia", last_name="Chen", email="parent@home.com")
    g.students.add(mine)
    for s in (mine, other):
        admin.post("/api/v1/transport/subscriptions/",
                   {"student": str(s.id), "zone": str(zone.id), "trip_type": "full_trip"}, format="json")

    parent = client_for(["parent"], email="parent@home.com")
    resp = parent.get("/api/v1/transport/subscriptions/")
    rows = resp.data["results"] if isinstance(resp.data, dict) else resp.data
    assert len(rows) == 1
    assert str(rows[0]["student"]) == str(mine.id)
