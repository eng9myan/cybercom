import uuid

import pytest
from rest_framework.test import APIClient

from products.cycom.appraisals.models import Appraisal
from products.cycom.hr.models import Employee


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


@pytest.fixture
def employee(db, tenant_id):
    return Employee.objects.create(
        tenant_id=tenant_id,
        employee_number="E-1",
        first_name="Jane",
        last_name="Doe",
        hire_date="2024-01-01",
    )


@pytest.mark.django_db
def test_create_appraisal(platform_admin_client, tenant_id, employee):
    resp = platform_admin_client.post(
        "/api/v1/appraisals/appraisals/",
        {
            "employee": str(employee.id),
            "period_start": "2026-01-01",
            "period_end": "2026-06-30",
        },
        format="json",
    )
    assert resp.status_code == 201, resp.data
    assert resp.data["status"] == "draft"


@pytest.mark.django_db
def test_complete_requires_rating(platform_admin_client, tenant_id, employee):
    appraisal = Appraisal.objects.create(
        tenant_id=tenant_id, employee=employee, period_start="2026-01-01", period_end="2026-06-30"
    )
    resp = platform_admin_client.post(f"/api/v1/appraisals/appraisals/{appraisal.id}/complete/")
    assert resp.status_code == 400


@pytest.mark.django_db
def test_complete_with_rating_succeeds(platform_admin_client, tenant_id, employee):
    appraisal = Appraisal.objects.create(
        tenant_id=tenant_id,
        employee=employee,
        period_start="2026-01-01",
        period_end="2026-06-30",
        rating=4,
    )
    resp = platform_admin_client.post(f"/api/v1/appraisals/appraisals/{appraisal.id}/complete/")
    assert resp.status_code == 200
    appraisal.refresh_from_db()
    assert appraisal.status == "completed"
    assert appraisal.completed_at is not None


@pytest.mark.django_db
def test_rating_out_of_range_rejected_at_full_clean(tenant_id, employee):
    appraisal = Appraisal(
        tenant_id=tenant_id,
        employee=employee,
        period_start="2026-01-01",
        period_end="2026-06-30",
        rating=9,
    )
    with pytest.raises(Exception):
        appraisal.full_clean()


@pytest.mark.django_db
def test_tenant_isolation(platform_admin_client, tenant_id, employee):
    other_tenant = uuid.uuid4()
    other_employee = Employee.objects.create(
        tenant_id=other_tenant,
        employee_number="E-2",
        first_name="Other",
        last_name="Tenant",
        hire_date="2024-01-01",
    )
    Appraisal.objects.create(
        tenant_id=other_tenant,
        employee=other_employee,
        period_start="2026-01-01",
        period_end="2026-06-30",
    )
    resp = platform_admin_client.get("/api/v1/appraisals/appraisals/")
    rows = resp.data["results"] if isinstance(resp.data, dict) else resp.data
    assert len(rows) == 0
