import uuid

import pytest
from rest_framework.test import APIClient

from products.cyed.curriculum.models import CurriculumOutcome


@pytest.fixture
def platform_admin_client(mint_token, mock_jwks, tenant_id):
    token = mint_token(
        {
            "sub": str(uuid.uuid4()),
            "email": "admin@cyed.edu.au",
            "tenant_id": str(tenant_id),
            "realm_access": {"roles": ["platform_admin"]},
        }
    )
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


@pytest.mark.django_db
def test_create_and_filter_outcome(platform_admin_client, tenant_id):
    resp = platform_admin_client.post(
        "/api/v1/curriculum/outcomes/",
        {"code": "AC9M8N01", "learning_area": "Mathematics", "year_level": 8,
         "strand": "Number", "content_description": "Recognise irrational numbers"},
        format="json",
    )
    assert resp.status_code == 201, resp.data

    listed = platform_admin_client.get("/api/v1/curriculum/outcomes/?learning_area=Mathematics&year_level=8")
    rows = listed.data["results"] if isinstance(listed.data, dict) else listed.data
    assert len(rows) == 1
    assert rows[0]["code"] == "AC9M8N01"


@pytest.mark.django_db
def test_duplicate_code_rejected(platform_admin_client, tenant_id):
    CurriculumOutcome.objects.create(tenant_id=tenant_id, code="AC9M8N01", learning_area="Mathematics")
    dup = platform_admin_client.post(
        "/api/v1/curriculum/outcomes/",
        {"code": "AC9M8N01", "learning_area": "Mathematics"},
        format="json",
    )
    assert dup.status_code == 400


@pytest.mark.django_db
def test_outcome_tenant_isolation(platform_admin_client, tenant_id):
    CurriculumOutcome.objects.create(tenant_id=uuid.uuid4(), code="AC9E7LA01", learning_area="English")
    resp = platform_admin_client.get("/api/v1/curriculum/outcomes/")
    rows = resp.data["results"] if isinstance(resp.data, dict) else resp.data
    assert all(r["code"] != "AC9E7LA01" for r in rows)
