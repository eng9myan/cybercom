import uuid
from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from products.cycom.field_service.models import ServiceContract, ServiceTask


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
def test_create_task_and_dispatch_transitions(admin_client, tenant_id):
    resp = admin_client.post(
        "/api/v1/field-service/tasks/",
        {
            "customer_name": "Acme Corp",
            "technician": "Sam",
            "scheduled_at": timezone.now().isoformat(),
        },
        format="json",
    )
    assert resp.status_code == 201, resp.data
    task_id = resp.data["id"]
    assert resp.data["status"] == "scheduled"

    resp = admin_client.post(f"/api/v1/field-service/tasks/{task_id}/transition/", {"status": "en_route"})
    assert resp.status_code == 200
    assert resp.data["status"] == "en_route"

    resp = admin_client.post(f"/api/v1/field-service/tasks/{task_id}/transition/", {"status": "done"})
    assert resp.status_code == 400  # can't skip in_progress


@pytest.mark.django_db
def test_complete_worksheet_requires_in_progress(admin_client, tenant_id):
    task = ServiceTask.objects.create(
        tenant_id=tenant_id, customer_name="Acme", scheduled_at=timezone.now()
    )
    resp = admin_client.post(
        f"/api/v1/field-service/tasks/{task.id}/complete-worksheet/",
        {"notes": "Fixed it", "signature": "sig"},
    )
    assert resp.status_code == 400

    task.status = "in_progress"
    task.save(update_fields=["status"])
    resp = admin_client.post(
        f"/api/v1/field-service/tasks/{task.id}/complete-worksheet/",
        {"notes": "Fixed it", "signature": "sig"},
    )
    assert resp.status_code == 200
    assert resp.data["status"] == "done"
    assert resp.data["completed_at"] is not None


@pytest.mark.django_db
def test_task_under_contract_gets_sla_deadline(admin_client, tenant_id):
    contract = ServiceContract.objects.create(
        tenant_id=tenant_id,
        customer_name="Acme Corp",
        contract_number="SC-1",
        start_date="2026-01-01",
        sla_hours=24,
    )
    scheduled = timezone.now()
    resp = admin_client.post(
        "/api/v1/field-service/tasks/",
        {
            "customer_name": "Acme Corp",
            "contract": str(contract.id),
            "scheduled_at": scheduled.isoformat(),
        },
        format="json",
    )
    assert resp.status_code == 201, resp.data
    assert resp.data["contract_number"] == "SC-1"
    assert resp.data["sla_deadline"] is not None
    assert resp.data["is_breached"] is False


@pytest.mark.django_db
def test_task_without_contract_never_breached(admin_client, tenant_id):
    resp = admin_client.post(
        "/api/v1/field-service/tasks/",
        {"customer_name": "Acme Corp", "scheduled_at": timezone.now().isoformat()},
        format="json",
    )
    assert resp.data["sla_deadline"] is None
    assert resp.data["is_breached"] is False


@pytest.mark.django_db
def test_task_breached_after_deadline_passes(tenant_id):
    contract = ServiceContract.objects.create(
        tenant_id=tenant_id, customer_name="Acme", contract_number="SC-2", start_date="2026-01-01", sla_hours=1
    )
    task = ServiceTask.objects.create(
        tenant_id=tenant_id,
        contract=contract,
        customer_name="Acme",
        scheduled_at=timezone.now() - timedelta(hours=3),
    )
    assert task.is_breached is True


@pytest.mark.django_db
def test_contract_unique_number_per_tenant(tenant_id):
    ServiceContract.objects.create(
        tenant_id=tenant_id, customer_name="A", contract_number="SC-DUP", start_date="2026-01-01", sla_hours=1
    )
    with pytest.raises(Exception):
        ServiceContract.objects.create(
            tenant_id=tenant_id, customer_name="B", contract_number="SC-DUP", start_date="2026-01-01", sla_hours=1
        )


@pytest.mark.django_db
def test_task_tenant_isolation(admin_client):
    ServiceTask.objects.create(
        tenant_id=uuid.uuid4(), customer_name="Foreign", scheduled_at=timezone.now()
    )
    resp = admin_client.get("/api/v1/field-service/tasks/")
    rows = resp.data["results"] if isinstance(resp.data, dict) else resp.data
    assert all(r["customer_name"] != "Foreign" for r in rows)
