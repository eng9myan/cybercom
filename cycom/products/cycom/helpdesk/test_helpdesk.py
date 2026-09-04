"""Helpdesk smoke coverage — CRUD via the API + tenant isolation."""

import uuid

import pytest
from rest_framework.test import APIClient

from products.cycom.helpdesk.models import Ticket


@pytest.fixture
def admin_client(mint_token, mock_jwks, tenant_id):
    token = mint_token(
        {
            "sub": str(uuid.uuid4()),
            "email": "admin@cybercom.io",
            "tenant_id": str(tenant_id),
            "realm_access": {"roles": ["platform_admin"]},
        }
    )
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


@pytest.mark.django_db
def test_create_and_list_ticket(admin_client, tenant_id):
    resp = admin_client.post(
        "/api/v1/helpdesk/tickets/",
        {"number": "T-1001", "subject": "POS printer offline", "priority": "high"},
        format="json",
    )
    assert resp.status_code == 201, resp.data
    assert resp.data["stage"] == "new"

    resp = admin_client.get("/api/v1/helpdesk/tickets/")
    rows = resp.data["results"] if isinstance(resp.data, dict) else resp.data
    assert any(r["number"] == "T-1001" for r in rows)


@pytest.mark.django_db
def test_ticket_tenant_isolation(admin_client):
    Ticket.objects.create(tenant_id=uuid.uuid4(), number="T-9999", subject="Foreign")
    resp = admin_client.get("/api/v1/helpdesk/tickets/")
    rows = resp.data["results"] if isinstance(resp.data, dict) else resp.data
    assert all(r["number"] != "T-9999" for r in rows)


@pytest.mark.django_db
def test_number_unique_per_tenant(admin_client, tenant_id):
    Ticket.objects.create(tenant_id=tenant_id, number="T-1", subject="First")
    # same number, different tenant is fine
    Ticket.objects.create(tenant_id=uuid.uuid4(), number="T-1", subject="Other tenant")
    with pytest.raises(Exception):
        Ticket.objects.create(tenant_id=tenant_id, number="T-1", subject="Dup")
