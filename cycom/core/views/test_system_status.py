"""Settings overview shows the tenant's real profile and integration state."""
import uuid

import pytest
from rest_framework.test import APIClient

from platform.tenant.models import Tenant, TenantProfile

pytestmark = pytest.mark.django_db


@pytest.fixture
def client(mint_token, mock_jwks, tenant_id):
    token = mint_token({"sub": str(uuid.uuid4()), "tenant_id": str(tenant_id),
                        "realm_access": {"roles": ["tenant_admin"]}})
    c = APIClient()
    c.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return c


def test_real_company_profile_and_currency_from_the_country_pack(client, tenant_id):
    t = Tenant.objects.create(id=tenant_id, name="acme", slug="acme", country_code="IT", timezone="Europe/Rome")
    TenantProfile.objects.create(tenant=t, legal_name="Acme Italia S.r.l.", vat_number="01234567890")
    resp = client.get("/api/v1/common/system-status/")
    assert resp.status_code == 200
    c = resp.data["company"]
    assert (c["name"], c["tax_id"], c["country_code"], c["timezone"]) == (
        "Acme Italia S.r.l.", "01234567890", "IT", "Europe/Rome")
    keys = {i["key"]: i for i in resp.data["integrations"]}
    assert keys["einvoicing"]["detail"].startswith("Italy")


def test_unconfigured_integrations_are_reported_as_such(client, tenant_id, monkeypatch, settings):
    Tenant.objects.create(id=tenant_id, name="acme2", slug="acme2", country_code="JO")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    settings.HYPERPAY_ENTITY_ID = ""
    resp = client.get("/api/v1/common/system-status/")
    keys = {i["key"]: i["status"] for i in resp.data["integrations"]}
    assert resp.data["company"]["currency"] == "JOD"
    assert keys["payments"] == "not_configured"
    assert keys["ai_documents"] == "not_configured"
    assert keys["email"] == "not_configured"      # test settings use the locmem backend
