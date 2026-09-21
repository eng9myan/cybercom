import uuid
from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from products.cycom.events.models import Event, Registration, TicketType


@pytest.fixture
def admin_client(mint_token, mock_jwks, tenant_id):
    token = mint_token(
        {
            "sub": str(uuid.uuid4()),
            "email": "events@cybercom.io",
            "tenant_id": str(tenant_id),
            "realm_access": {"roles": ["platform_admin"]},
        }
    )
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


@pytest.fixture
def event(db, tenant_id):
    now = timezone.now()
    return Event.objects.create(
        tenant_id=tenant_id, name="Annual Conference", start_at=now, end_at=now + timedelta(hours=8),
        capacity=2,
    )


@pytest.mark.django_db
def test_register_attendee(admin_client, tenant_id, event):
    resp = admin_client.post(
        f"/api/v1/events/events/{event.id}/register/",
        {"attendee_name": "Jane Doe", "attendee_email": "jane@x.com"},
        format="json",
    )
    assert resp.status_code == 201, resp.data
    assert resp.data["status"] == "registered"


@pytest.mark.django_db
def test_registration_blocked_once_event_sold_out(admin_client, tenant_id, event):
    Registration.objects.create(tenant_id=tenant_id, event=event, attendee_name="A")
    Registration.objects.create(tenant_id=tenant_id, event=event, attendee_name="B")

    resp = admin_client.post(
        f"/api/v1/events/events/{event.id}/register/", {"attendee_name": "C"}, format="json"
    )
    assert resp.status_code == 400


@pytest.mark.django_db
def test_cancelled_registration_frees_capacity(admin_client, tenant_id, event):
    r1 = Registration.objects.create(tenant_id=tenant_id, event=event, attendee_name="A")
    Registration.objects.create(tenant_id=tenant_id, event=event, attendee_name="B")
    r1.status = "cancelled"
    r1.save(update_fields=["status"])

    resp = admin_client.post(
        f"/api/v1/events/events/{event.id}/register/", {"attendee_name": "C"}, format="json"
    )
    assert resp.status_code == 201, resp.data


@pytest.mark.django_db
def test_unlimited_capacity_never_sold_out(admin_client, tenant_id):
    now = timezone.now()
    event = Event.objects.create(
        tenant_id=tenant_id, name="Open House", start_at=now, end_at=now, capacity=0
    )
    for i in range(10):
        Registration.objects.create(tenant_id=tenant_id, event=event, attendee_name=f"P{i}")
    resp = admin_client.post(
        f"/api/v1/events/events/{event.id}/register/", {"attendee_name": "Extra"}, format="json"
    )
    assert resp.status_code == 201


@pytest.mark.django_db
def test_ticket_type_capacity_independent_of_event_capacity(admin_client, tenant_id):
    now = timezone.now()
    event = Event.objects.create(
        tenant_id=tenant_id, name="Concert", start_at=now, end_at=now, capacity=100
    )
    vip = TicketType.objects.create(
        tenant_id=tenant_id, event=event, name="VIP", price=200, quantity_available=1
    )
    Registration.objects.create(tenant_id=tenant_id, event=event, ticket_type=vip, attendee_name="A")

    resp = admin_client.post(
        f"/api/v1/events/events/{event.id}/register/",
        {"attendee_name": "B", "ticket_type": str(vip.id)},
        format="json",
    )
    assert resp.status_code == 400  # VIP sold out even though event has room


@pytest.mark.django_db
def test_check_in_then_cannot_cancel(admin_client, tenant_id, event):
    reg = Registration.objects.create(tenant_id=tenant_id, event=event, attendee_name="A")
    resp = admin_client.post(f"/api/v1/events/registrations/{reg.id}/check-in/")
    assert resp.status_code == 200
    assert resp.data["status"] == "checked_in"
    assert resp.data["checked_in_at"] is not None

    resp = admin_client.post(f"/api/v1/events/registrations/{reg.id}/cancel/")
    assert resp.status_code == 400


@pytest.mark.django_db
def test_cannot_check_in_twice(admin_client, tenant_id, event):
    reg = Registration.objects.create(tenant_id=tenant_id, event=event, attendee_name="A")
    admin_client.post(f"/api/v1/events/registrations/{reg.id}/check-in/")
    resp = admin_client.post(f"/api/v1/events/registrations/{reg.id}/check-in/")
    assert resp.status_code == 400


@pytest.mark.django_db
def test_tenant_isolation(admin_client):
    now = timezone.now()
    Event.objects.create(tenant_id=uuid.uuid4(), name="Foreign Event", start_at=now, end_at=now)
    resp = admin_client.get("/api/v1/events/events/")
    rows = resp.data["results"] if isinstance(resp.data, dict) else resp.data
    assert all(r["name"] != "Foreign Event" for r in rows)
