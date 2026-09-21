import uuid

import pytest
from rest_framework.test import APIClient

from products.cycom.project.models import Project, Task, TimesheetEntry


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


@pytest.mark.django_db
def test_create_timesheet_entry_rolls_up_task_hours(platform_admin_client, tenant_id):
    task = Task.objects.create(tenant_id=tenant_id, name="Wire dashboard")

    resp = platform_admin_client.post(
        "/api/v1/project/timesheets/",
        {"task": str(task.id), "employee_name": "Jane Doe", "date": "2026-09-21", "hours": "3.5"},
        format="json",
    )
    assert resp.status_code == 201, resp.data

    resp = platform_admin_client.post(
        "/api/v1/project/timesheets/",
        {"task": str(task.id), "employee_name": "Jane Doe", "date": "2026-09-22", "hours": "2"},
        format="json",
    )
    assert resp.status_code == 201, resp.data

    task.refresh_from_db()
    assert task.effective_hours == pytest.approx(5.5)


@pytest.mark.django_db
def test_timesheet_list_is_bare_array(platform_admin_client, tenant_id):
    task = Task.objects.create(tenant_id=tenant_id, name="Wire dashboard")
    TimesheetEntry.objects.create(tenant_id=tenant_id, task=task, date="2026-09-21", hours=1)
    resp = platform_admin_client.get("/api/v1/project/timesheets/")
    assert resp.status_code == 200
    assert isinstance(resp.data, list)


@pytest.mark.django_db
def test_deleting_timesheet_entry_recalculates_task_hours(platform_admin_client, tenant_id):
    task = Task.objects.create(tenant_id=tenant_id, name="Wire dashboard")
    e1 = TimesheetEntry.objects.create(tenant_id=tenant_id, task=task, date="2026-09-21", hours=3)
    TimesheetEntry.objects.create(tenant_id=tenant_id, task=task, date="2026-09-22", hours=2)
    task.refresh_from_db()
    assert task.effective_hours == pytest.approx(5)

    e1.delete()
    task.refresh_from_db()
    assert task.effective_hours == pytest.approx(2)


@pytest.mark.django_db
def test_timesheet_entry_without_task_does_not_error(platform_admin_client, tenant_id):
    resp = platform_admin_client.post(
        "/api/v1/project/timesheets/",
        {"employee_name": "Jane Doe", "date": "2026-09-21", "hours": "1"},
        format="json",
    )
    assert resp.status_code == 201, resp.data


@pytest.mark.django_db
def test_timesheet_tenant_isolation(platform_admin_client, tenant_id):
    other = uuid.uuid4()
    TimesheetEntry.objects.create(tenant_id=other, date="2026-09-21", hours=1, employee_name="Other")
    resp = platform_admin_client.get("/api/v1/project/timesheets/")
    assert all(r["employee_name"] != "Other" for r in resp.data)
