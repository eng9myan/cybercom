"""Post-setup Approval Policy editing API (audit follow-up to HR-4): the
setup wizard's Approvals step was preview-only, and once provisioned there
was no way to change a threshold or approver role without hand-editing the
DB. `ApprovalPolicyViewSet` (list/retrieve/patch, tiers replaced whole) closes
that gap."""

import uuid
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from platform.provisioning.models import ApprovalPolicy, ApprovalTier


def _policy(tenant_id, doc_type="purchase_request"):
    p = ApprovalPolicy.objects.create(
        tenant_id=tenant_id, document_type=doc_type, name="Purchase Request Approval"
    )
    ApprovalTier.objects.create(
        tenant_id=tenant_id, policy=p, sequence=1,
        threshold_min=0, threshold_max=500, approver_role="Department Manager",
    )
    ApprovalTier.objects.create(
        tenant_id=tenant_id, policy=p, sequence=2,
        threshold_min=500, threshold_max=None, approver_role="General Manager",
    )
    return p


@pytest.fixture
def authed_client(mint_token, mock_jwks, tenant_id):
    token = mint_token({
        "sub": str(uuid.uuid4()),
        "email": "gm@cybercom.io",
        "tenant_id": str(tenant_id),
        "realm_access": {"roles": ["general_manager"]},
    })
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client, tenant_id


@pytest.mark.django_db
def test_list_only_returns_own_tenant_policies(authed_client):
    client, tenant_id = authed_client
    _policy(tenant_id)
    _policy(uuid.uuid4())  # another tenant — must not leak
    resp = client.get("/api/v1/provisioning/approval-policies/")
    assert resp.status_code == 200
    rows = resp.json()["results"] if isinstance(resp.json(), dict) else resp.json()
    assert len(rows) == 1
    assert rows[0]["document_type"] == "purchase_request"


@pytest.mark.django_db
def test_patch_replaces_tiers(authed_client):
    client, tenant_id = authed_client
    policy = _policy(tenant_id)
    resp = client.patch(
        f"/api/v1/provisioning/approval-policies/{policy.id}/",
        {
            "tiers": [
                {"sequence": 1, "threshold_min": "0", "threshold_max": "1000", "approver_role": "Branch Manager"},
                {"sequence": 2, "threshold_min": "1000", "threshold_max": None, "approver_role": "CFO"},
            ]
        },
        format="json",
    )
    assert resp.status_code == 200, resp.content
    policy.refresh_from_db()
    tiers = list(policy.tiers.order_by("sequence"))
    assert len(tiers) == 2
    assert tiers[0].threshold_max == Decimal("1000")
    assert tiers[0].approver_role == "Branch Manager"
    assert tiers[1].threshold_max is None
    assert tiers[1].approver_role == "CFO"


@pytest.mark.django_db
def test_patch_can_disable_without_touching_tiers(authed_client):
    client, tenant_id = authed_client
    policy = _policy(tenant_id)
    resp = client.patch(
        f"/api/v1/provisioning/approval-policies/{policy.id}/",
        {"is_active": False},
        format="json",
    )
    assert resp.status_code == 200, resp.content
    policy.refresh_from_db()
    assert policy.is_active is False
    assert policy.tiers.count() == 2  # untouched — tiers omitted from payload


@pytest.mark.django_db
def test_patch_rejects_non_final_open_ended_tier(authed_client):
    client, tenant_id = authed_client
    policy = _policy(tenant_id)
    resp = client.patch(
        f"/api/v1/provisioning/approval-policies/{policy.id}/",
        {
            "tiers": [
                {"sequence": 1, "threshold_min": "0", "threshold_max": None, "approver_role": "A"},
                {"sequence": 2, "threshold_min": "0", "threshold_max": "100", "approver_role": "B"},
            ]
        },
        format="json",
    )
    assert resp.status_code == 400


@pytest.mark.django_db
def test_cannot_create_or_delete_via_api(authed_client):
    client, tenant_id = authed_client
    policy = _policy(tenant_id)
    resp = client.post("/api/v1/provisioning/approval-policies/", {"document_type": "payment", "name": "x"}, format="json")
    assert resp.status_code == 405
    resp = client.delete(f"/api/v1/provisioning/approval-policies/{policy.id}/")
    assert resp.status_code == 405
