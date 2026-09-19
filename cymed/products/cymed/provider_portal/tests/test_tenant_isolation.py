"""
provider_portal's 3 viewsets shipped with `queryset = Model.objects.all()` and
no get_queryset() tenant filter — unlike every other viewset in this codebase.
These tests prove the fix: a tenant can only ever see its own rows.
"""
import uuid

import pytest
from rest_framework.test import APIClient

from products.cymed.core.providers.models import Provider, ProviderType
from products.cymed.provider_portal.models import (
    ProviderCredentialingStatus,
    ProviderPortalActivity,
    ProviderPortalProfile,
)


def _auth_client(tenant_id, mint_token, mock_jwks):
    client = APIClient()
    token = mint_token({
        "sub": str(uuid.uuid4()),
        "email": "doctor@cymed.io",
        "tenant_id": str(tenant_id),
        "realm_access": {"roles": ["platform_admin"]},
        "roles": ["platform_admin"],
        "permissions": ["read", "write"],
    })
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}", HTTP_X_TENANT_ID=str(tenant_id))
    return client


def _provider(tenant_id, npi):
    return Provider.objects.create(
        tenant_id=tenant_id, user_id=uuid.uuid4(), first_name="A", last_name="B",
        provider_type=ProviderType.PHYSICIAN, npi=npi,
    )


@pytest.mark.django_db
def test_profile_list_is_tenant_isolated(mint_token, mock_jwks):
    tenant_a, tenant_b = uuid.uuid4(), uuid.uuid4()
    provider_a = _provider(tenant_a, "NPI-A-1")
    provider_b = _provider(tenant_b, "NPI-B-1")
    ProviderPortalProfile.objects.create(tenant_id=tenant_a, provider=provider_a)
    ProviderPortalProfile.objects.create(tenant_id=tenant_b, provider=provider_b)

    resp = _auth_client(tenant_a, mint_token, mock_jwks).get("/api/v1/provider-portal/profiles/")
    assert resp.status_code == 200
    ids = {row["id"] for row in resp.data.get("results", resp.data)}
    tenant_a_ids = set(
        ProviderPortalProfile.objects.filter(tenant_id=tenant_a).values_list("id", flat=True)
    )
    assert ids == {str(i) for i in tenant_a_ids} or ids == tenant_a_ids


@pytest.mark.django_db
def test_profile_detail_404s_across_tenants(mint_token, mock_jwks):
    tenant_a, tenant_b = uuid.uuid4(), uuid.uuid4()
    provider_b = _provider(tenant_b, "NPI-B-2")
    profile_b = ProviderPortalProfile.objects.create(tenant_id=tenant_b, provider=provider_b)

    resp = _auth_client(tenant_a, mint_token, mock_jwks).get(
        f"/api/v1/provider-portal/profiles/{profile_b.id}/"
    )
    assert resp.status_code == 404


@pytest.mark.django_db
def test_activity_list_is_tenant_isolated(mint_token, mock_jwks):
    tenant_a, tenant_b = uuid.uuid4(), uuid.uuid4()
    provider_a = _provider(tenant_a, "NPI-A-3")
    provider_b = _provider(tenant_b, "NPI-B-3")
    profile_a = ProviderPortalProfile.objects.create(tenant_id=tenant_a, provider=provider_a)
    profile_b = ProviderPortalProfile.objects.create(tenant_id=tenant_b, provider=provider_b)
    ProviderPortalActivity.objects.create(
        tenant_id=tenant_a, profile=profile_a, activity_type="login"
    )
    ProviderPortalActivity.objects.create(
        tenant_id=tenant_b, profile=profile_b, activity_type="login"
    )

    resp = _auth_client(tenant_a, mint_token, mock_jwks).get("/api/v1/provider-portal/activities/")
    assert resp.status_code == 200
    rows = resp.data.get("results", resp.data)
    assert len(rows) == 1


@pytest.mark.django_db
def test_credentialing_list_is_tenant_isolated(mint_token, mock_jwks):
    tenant_a, tenant_b = uuid.uuid4(), uuid.uuid4()
    provider_a = _provider(tenant_a, "NPI-A-4")
    provider_b = _provider(tenant_b, "NPI-B-4")
    ProviderCredentialingStatus.objects.create(tenant_id=tenant_a, provider=provider_a)
    ProviderCredentialingStatus.objects.create(tenant_id=tenant_b, provider=provider_b)

    resp = _auth_client(tenant_a, mint_token, mock_jwks).get("/api/v1/provider-portal/credentialing/")
    assert resp.status_code == 200
    rows = resp.data.get("results", resp.data)
    assert len(rows) == 1
