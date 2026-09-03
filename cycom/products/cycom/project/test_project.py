import uuid

import pytest
from rest_framework.test import APIClient

from products.cycom.project.models import Project, Task


@pytest.fixture
def platform_admin_client(mint_token, mock_jwks, tenant_id):
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
def test_create_and_list_task(platform_admin_client, tenant_id):
    project = Project.objects.create(tenant_id=tenant_id, name="Launch Prep")

    resp = platform_admin_client.post(
        "/api/v1/project/tasks/",
        {"name": "Wire dashboard", "project": str(project.id), "allocated_hours": "8"},
        format="json",
    )
    assert resp.status_code == 201, resp.data
    task_id = resp.data["id"]

    resp = platform_admin_client.get("/api/v1/project/tasks/")
    assert resp.status_code == 200
    rows = resp.data["results"] if isinstance(resp.data, dict) else resp.data
    assert any(r["id"] == task_id for r in rows)


@pytest.mark.django_db
def test_task_tenant_isolation(platform_admin_client, tenant_id):
    other = uuid.uuid4()
    Task.objects.create(tenant_id=other, name="Foreign task")
    resp = platform_admin_client.get("/api/v1/project/tasks/")
    rows = resp.data["results"] if isinstance(resp.data, dict) else resp.data
    assert all(r["name"] != "Foreign task" for r in rows)
