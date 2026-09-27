"""
Catalog viewsets (country/department/industry packs) must return their
full list unpaginated -- they're small, bounded reference data a picker UI
consumes in full. With the project's default page size (25) this silently
truncated IndustryTemplate below 25 rows before anyone noticed at this
catalog's original, smaller size; these tests pin the fix so it can't
regress the same way again.
"""

import uuid

import pytest
from django.core.management import call_command
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def seeded_packs(db):
    call_command("seed_packs")


@pytest.fixture
def client(mint_token, mock_jwks):
    token = mint_token({
        "sub": str(uuid.uuid4()),
        "email": "gm@cybercom.io",
        "tenant_id": str(uuid.uuid4()),
        "realm_access": {"roles": ["tenant_admin"]},
    })
    c = APIClient()
    c.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return c


def test_industry_templates_returns_all_66_unpaginated(client):
    resp = client.get("/api/v1/provisioning/industry-templates/")
    assert resp.status_code == 200
    assert isinstance(resp.data, list), "expected a bare array, not a paginated envelope"
    assert len(resp.data) >= 66


def test_country_packs_returns_all_12_unpaginated(client):
    resp = client.get("/api/v1/provisioning/country-packs/")
    assert resp.status_code == 200
    assert isinstance(resp.data, list)
    assert len(resp.data) >= 12


def test_department_packs_returns_all_unpaginated(client):
    resp = client.get("/api/v1/provisioning/department-packs/")
    assert resp.status_code == 200
    assert isinstance(resp.data, list)
    assert len(resp.data) >= 10


def test_catalog_endpoints_require_auth():
    anon = APIClient()
    assert anon.get("/api/v1/provisioning/industry-templates/").status_code == 401
    assert anon.get("/api/v1/provisioning/country-packs/").status_code == 401
