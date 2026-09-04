"""Recruitment smoke coverage — CRUD via the API + tenant isolation."""

import uuid

import pytest
from rest_framework.test import APIClient

from products.cycom.recruitment.models import Applicant


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
def test_create_and_list_applicant(admin_client, tenant_id):
    resp = admin_client.post(
        "/api/v1/recruitment/applicants/",
        {"name": "Layla Q", "job_title": "Cashier", "email": "layla@example.com"},
        format="json",
    )
    assert resp.status_code == 201, resp.data
    assert resp.data["stage"] == "new"

    resp = admin_client.get("/api/v1/recruitment/applicants/")
    rows = resp.data["results"] if isinstance(resp.data, dict) else resp.data
    assert any(r["name"] == "Layla Q" for r in rows)


@pytest.mark.django_db
def test_stage_filter(admin_client, tenant_id):
    Applicant.objects.create(tenant_id=tenant_id, name="A", job_title="Cook", stage="interview")
    Applicant.objects.create(tenant_id=tenant_id, name="B", job_title="Cook", stage="new")
    resp = admin_client.get("/api/v1/recruitment/applicants/?stage=interview")
    rows = resp.data["results"] if isinstance(resp.data, dict) else resp.data
    assert [r["name"] for r in rows] == ["A"]


@pytest.mark.django_db
def test_applicant_tenant_isolation(admin_client):
    Applicant.objects.create(tenant_id=uuid.uuid4(), name="Foreign", job_title="X")
    resp = admin_client.get("/api/v1/recruitment/applicants/")
    rows = resp.data["results"] if isinstance(resp.data, dict) else resp.data
    assert all(r["name"] != "Foreign" for r in rows)
