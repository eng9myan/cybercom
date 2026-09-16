import uuid

import pytest
from rest_framework.test import APIClient

from products.cyed.events.models import Event
from products.cyed.sis.models import Guardian, Student


@pytest.fixture
def client_for(mint_token, mock_jwks, tenant_id):
    def _make(roles, email="u@cyed.edu.au"):
        token = mint_token({"sub": str(uuid.uuid4()), "email": email, "tenant_id": str(tenant_id),
                            "realm_access": {"roles": roles}})
        c = APIClient()
        c.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        return c
    return _make


@pytest.mark.django_db
def test_event_create_staff_and_parent_scoped_participation(client_for, tenant_id):
    admin = client_for(["tenant_admin"])
    ev = admin.post("/api/v1/events/events/",
                    {"name": "Zoo Excursion", "event_type": "excursion", "requires_consent": True}, format="json")
    assert ev.status_code == 201, ev.data

    child = Student.objects.create(tenant_id=tenant_id, first_name="Ivy", last_name="Chen", year_level=8)
    other = Student.objects.create(tenant_id=tenant_id, first_name="Sam", last_name="Other", year_level=8)
    g = Guardian.objects.create(tenant_id=tenant_id, first_name="Jia", last_name="Chen", email="parent@home.com")
    g.students.add(child)
    event = Event.objects.get(id=ev.data["id"])
    from products.cyed.events.models import EventParticipation
    EventParticipation.objects.create(tenant_id=tenant_id, event=event, student=child, status="invited")
    EventParticipation.objects.create(tenant_id=tenant_id, event=event, student=other, status="invited")

    parent = client_for(["parent"], email="parent@home.com")
    rows = parent.get("/api/v1/events/participations/").data
    rows = rows["results"] if isinstance(rows, dict) else rows
    assert len(rows) == 1
    # Parent can confirm + consent for their own child.
    upd = parent.patch(f"/api/v1/events/participations/{rows[0]['id']}/",
                       {"status": "confirmed", "consent_given": True}, format="json")
    assert upd.status_code == 200
    assert upd.data["consent_given"] is True
