"""
TenantIsolationMiddleware must take the tenant from the verified token, not
from the X-Tenant-ID header. Before the 2026-10-02 fix the header won, so a
tenant-A token with `X-Tenant-ID: <B>` was served as tenant B by every
queryset and by the Postgres RLS GUC alike.

Path-agnostic on purpose: the middleware answers before URL resolution, so
an unrouted path shows the decision without depending on any one app.
"""
import uuid

import pytest
from rest_framework.test import APIClient

PATH = "/api/v1/tenant-binding-probe/"
MISMATCH = "X-Tenant-ID does not match the authenticated tenant."


def _client(mint_token, token_tenant, header_tenant, roles=("teacher",)):
    tok = mint_token({
        "sub": str(uuid.uuid4()), "email": "u@example.com", "tenant_id": str(token_tenant),
        "realm_access": {"roles": list(roles)}, "roles": list(roles),
    })
    c = APIClient()
    c.credentials(HTTP_AUTHORIZATION=f"Bearer {tok}", HTTP_X_TENANT_ID=str(header_tenant))
    return c


@pytest.mark.django_db
def test_header_naming_another_tenant_is_rejected(mint_token, mock_jwks):
    a, b = uuid.uuid4(), uuid.uuid4()
    resp = _client(mint_token, a, b).get(PATH)
    assert resp.status_code == 403
    assert resp.json()["detail"] == MISMATCH


@pytest.mark.django_db
def test_header_matching_the_token_passes(mint_token, mock_jwks):
    a = uuid.uuid4()
    resp = _client(mint_token, a, a).get(PATH)
    assert resp.status_code != 403


@pytest.mark.django_db
def test_platform_admin_may_select_another_tenant(mint_token, mock_jwks):
    a, b = uuid.uuid4(), uuid.uuid4()
    resp = _client(mint_token, a, b, roles=("platform_admin",)).get(PATH)
    assert resp.status_code != 403
