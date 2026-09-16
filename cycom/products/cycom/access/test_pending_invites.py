"""Team & Roles invite-by-email resolution (audit follow-up): RoleAssignment.
user_id must be a real Keycloak sub, which doesn't exist until someone logs
in — so an admin inviting a not-yet-registered teammate stores a
"pending:<email>" placeholder. resolve_pending_invites() swaps it for the
real sub the first time that person is seen with a verified token, hooked
into RoleAssignmentViewSet.get_queryset (the Team page's own list call)."""

import uuid

import pytest
from rest_framework.test import APIClient

from products.cycom.access.models import Role, RoleAssignment
from products.cycom.access.services import resolve_pending_invites


def _client(mint_token, mock_jwks, tenant_id, user_id, email=None, roles=None):
    token = mint_token(
        {
            "sub": user_id,
            "email": email or f"{user_id}@cybercom.io",
            "tenant_id": str(tenant_id),
            "realm_access": {"roles": roles or ["platform_admin"]},
        }
    )
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


@pytest.mark.django_db
def test_resolve_pending_invites_swaps_placeholder_for_real_sub(tenant_id):
    role = Role.objects.create(tenant_id=tenant_id, name="Cashier")
    pending = RoleAssignment.objects.create(
        tenant_id=tenant_id, user_id="pending:newhire@acme.com", role=role
    )

    count = resolve_pending_invites(tenant_id, "real-sub-123", "newhire@acme.com")

    assert count == 1
    pending.refresh_from_db()
    assert pending.user_id == "real-sub-123"


@pytest.mark.django_db
def test_resolve_is_case_insensitive_on_email(tenant_id):
    role = Role.objects.create(tenant_id=tenant_id, name="Cashier")
    pending = RoleAssignment.objects.create(
        tenant_id=tenant_id, user_id="pending:NewHire@Acme.com", role=role
    )

    resolve_pending_invites(tenant_id, "real-sub-123", "newhire@acme.com")

    pending.refresh_from_db()
    assert pending.user_id == "real-sub-123"


@pytest.mark.django_db
def test_resolve_is_noop_when_nothing_pending(tenant_id):
    assert resolve_pending_invites(tenant_id, "real-sub-123", "nobody@acme.com") == 0


@pytest.mark.django_db
def test_resolve_is_noop_without_email_or_user_id(tenant_id):
    role = Role.objects.create(tenant_id=tenant_id, name="Cashier")
    RoleAssignment.objects.create(tenant_id=tenant_id, user_id="pending:x@acme.com", role=role)
    assert resolve_pending_invites(tenant_id, "real-sub", "") == 0
    assert resolve_pending_invites(tenant_id, "", "x@acme.com") == 0


@pytest.mark.django_db
def test_team_page_list_call_resolves_own_pending_invite(mint_token, mock_jwks, tenant_id):
    role = Role.objects.create(tenant_id=tenant_id, name="Cashier")
    pending = RoleAssignment.objects.create(
        tenant_id=tenant_id, user_id="pending:newhire@acme.com", role=role
    )

    client = _client(mint_token, mock_jwks, tenant_id, "real-sub-123", email="newhire@acme.com")
    resp = client.get("/api/v1/access/role-assignments/")
    assert resp.status_code == 200, resp.content

    pending.refresh_from_db()
    assert pending.user_id == "real-sub-123"


@pytest.mark.django_db
def test_resolution_does_not_touch_other_tenants_pending_invites(mint_token, mock_jwks, tenant_id):
    other_tenant = uuid.uuid4()
    role = Role.objects.create(tenant_id=other_tenant, name="Cashier")
    other_pending = RoleAssignment.objects.create(
        tenant_id=other_tenant, user_id="pending:newhire@acme.com", role=role
    )

    client = _client(mint_token, mock_jwks, tenant_id, "real-sub-123", email="newhire@acme.com")
    client.get("/api/v1/access/role-assignments/")

    other_pending.refresh_from_db()
    assert other_pending.user_id == "pending:newhire@acme.com"
