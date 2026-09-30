"""
Shared platform.audit API as seen from cycom (claims-based auth):
audit readers get their own tenant's trail -- the list endpoints used to
403 for every cycom caller -- and never another tenant's, whether by
listing, searching with a crafted tenant_id, exporting or verifying chains.
"""
import uuid

import pytest
from rest_framework.test import APIClient

from platform.audit.models import AuditChain, AuditEvent
from platform.audit.services import AuditService

pytestmark = pytest.mark.django_db


@pytest.fixture
def client_for(mint_token, mock_jwks):
    def make(tid, roles=("tenant_admin",)):
        token = mint_token({"sub": str(uuid.uuid4()), "tenant_id": str(tid), "realm_access": {"roles": list(roles)}})
        c = APIClient()
        c.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        return c
    return make


def _rows(resp):
    return resp.data["results"] if isinstance(resp.data, dict) and "results" in resp.data else resp.data


@pytest.fixture
def two_tenants(tenant_id):
    other = uuid.uuid4()
    svc = AuditService()
    svc.record(action="update", action_verb="updated", resource_type="invoice", resource_id="mine",
               tenant_id=tenant_id, actor_user_id="alice")
    svc.record(action="update", action_verb="updated", resource_type="invoice", resource_id="theirs",
               tenant_id=other, actor_user_id="mallory")
    return tenant_id, other


def test_tenant_admin_can_now_list_its_own_audit_events(two_tenants, client_for):
    mine, _ = two_tenants
    resp = client_for(mine).get("/api/v1/audit/events/")
    assert resp.status_code == 200, resp.content
    assert {r["resource_id"] for r in _rows(resp)} == {"mine"}


def test_other_tenants_events_are_not_reachable_by_id(two_tenants, client_for):
    mine, other = two_tenants
    theirs = AuditEvent.objects.get(tenant_id=other)
    assert client_for(mine).get(f"/api/v1/audit/events/{theirs.id}/").status_code == 404


def test_search_ignores_a_crafted_tenant_id(two_tenants, client_for):
    mine, other = two_tenants
    resp = client_for(mine).post("/api/v1/audit/events/search/", {"tenant_id": str(other)}, format="json")
    assert resp.status_code == 200
    assert {r["resource_id"] for r in resp.data} <= {"mine"}


def test_plain_users_cannot_read_audit_trails(two_tenants, client_for):
    mine, _ = two_tenants
    assert client_for(mine, roles=("sales_rep",)).get("/api/v1/audit/events/").status_code == 403


def test_platform_admin_still_sees_across_tenants(two_tenants, client_for):
    mine, _ = two_tenants
    resp = client_for(mine, roles=("platform_admin",)).get("/api/v1/audit/events/")
    assert {r["resource_id"] for r in _rows(resp)} == {"mine", "theirs"}


def test_verify_chain_is_limited_to_own_chains(two_tenants, client_for):
    mine, other = two_tenants
    c = client_for(mine, roles=("audit_admin",))
    resp = c.post("/api/v1/audit/events/verify_chain/", {}, format="json")
    assert resp.status_code == 200 and isinstance(resp.data, list)
    own_keys = set(AuditChain.objects.filter(tenant_id=mine).values_list("chain_key", flat=True))
    assert {r["chain_key"] for r in resp.data} == own_keys
    their_key = AuditChain.objects.get(tenant_id=other).chain_key
    probe = c.post("/api/v1/audit/events/verify_chain/", {"chain_key": their_key}, format="json")
    assert probe.data["error"] == "chain_not_found"
