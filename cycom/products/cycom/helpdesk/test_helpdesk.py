"""Helpdesk smoke coverage — CRUD via the API + tenant isolation."""

import uuid
from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from products.cycom.helpdesk.models import SLAPolicy, Ticket


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


@pytest.mark.django_db
def test_ticket_created_with_matching_sla_policy(admin_client, tenant_id):
    SLAPolicy.objects.create(
        tenant_id=tenant_id, name="Urgent — 4h", priority="urgent", resolution_hours=4
    )
    SLAPolicy.objects.create(tenant_id=tenant_id, name="Default — 48h", resolution_hours=48)

    resp = admin_client.post(
        "/api/v1/helpdesk/tickets/",
        {"number": "T-2001", "subject": "Server down", "priority": "urgent"},
        format="json",
    )
    assert resp.status_code == 201, resp.data
    assert resp.data["sla_policy_name"] == "Urgent — 4h"
    assert resp.data["sla_deadline"] is not None
    assert resp.data["is_breached"] is False


@pytest.mark.django_db
def test_ticket_falls_back_to_generic_policy(admin_client, tenant_id):
    SLAPolicy.objects.create(
        tenant_id=tenant_id, name="Urgent — 4h", priority="urgent", resolution_hours=4
    )
    SLAPolicy.objects.create(tenant_id=tenant_id, name="Default — 48h", resolution_hours=48)

    resp = admin_client.post(
        "/api/v1/helpdesk/tickets/",
        {"number": "T-2002", "subject": "Password reset", "priority": "low"},
        format="json",
    )
    assert resp.status_code == 201, resp.data
    assert resp.data["sla_policy_name"] == "Default — 48h"


@pytest.mark.django_db
def test_ticket_is_breached_once_deadline_passes(tenant_id):
    policy = SLAPolicy.objects.create(tenant_id=tenant_id, name="1h", resolution_hours=1)
    ticket = Ticket.objects.create(
        tenant_id=tenant_id, number="T-3001", subject="X", sla_policy=policy
    )
    ticket.sla_deadline = timezone.now() - timedelta(hours=1)
    ticket.save(update_fields=["sla_deadline"])
    assert ticket.is_breached is True


@pytest.mark.django_db
def test_resolved_before_deadline_is_not_breached(admin_client, tenant_id):
    SLAPolicy.objects.create(tenant_id=tenant_id, name="48h", resolution_hours=48)
    resp = admin_client.post(
        "/api/v1/helpdesk/tickets/",
        {"number": "T-3002", "subject": "X", "priority": "normal"},
        format="json",
    )
    ticket_id = resp.data["id"]
    resp = admin_client.patch(
        f"/api/v1/helpdesk/tickets/{ticket_id}/", {"stage": "solved"}, format="json"
    )
    assert resp.status_code == 200
    assert resp.data["resolved_at"] is not None
    assert resp.data["is_breached"] is False


@pytest.mark.django_db
def test_resolved_after_deadline_stays_breached(tenant_id):
    policy = SLAPolicy.objects.create(tenant_id=tenant_id, name="1h", resolution_hours=1)
    ticket = Ticket.objects.create(
        tenant_id=tenant_id, number="T-3003", subject="X", sla_policy=policy
    )
    ticket.sla_deadline = timezone.now() - timedelta(hours=2)
    ticket.save(update_fields=["sla_deadline"])
    ticket.stage = "solved"
    ticket.save()
    ticket.refresh_from_db()
    assert ticket.resolved_at is not None
    assert ticket.is_breached is True
