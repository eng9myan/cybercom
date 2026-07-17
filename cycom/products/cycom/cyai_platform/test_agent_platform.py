import uuid

import pytest
from rest_framework.test import APIClient

from products.cycom.cyai_platform.models import AgentDefinition, AgentEntitlement
from products.cycom.cyai_platform.services import (
    grant_entitlement,
    has_active_entitlement,
    revoke_entitlement,
    route_question,
)


def _client(mint_token, mock_jwks, tenant_id, user_id, roles=None):
    token = mint_token(
        {
            "sub": user_id,
            "email": f"{user_id}@cybercom.io",
            "tenant_id": str(tenant_id),
            "realm_access": {"roles": roles or []},
        }
    )
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


@pytest.mark.django_db
def test_three_agents_seeded():
    keys = set(AgentDefinition.objects.values_list("agent_key", flat=True))
    assert keys == {"ask_cycom", "report_studio", "builder_ai"}


@pytest.mark.django_db
@pytest.mark.parametrize(
    "question,expected_agent",
    [
        ("What were sales for Amman branch yesterday?", "ask_cycom"),
        ("Open invoice INV-2026-00482.", "ask_cycom"),
        ("Show all customer projects with incomplete demand data.", "ask_cycom"),
        ("Create a permanent weekly sales dashboard", "report_studio"),
        ("Create a report comparing monthly sales by branch, product category, and salesperson.", "report_studio"),
        ("Create a reusable cost-to-serve comparison by customer and lane.", "report_studio"),
        ("Build a customer credit approval workflow", "builder_ai"),
        ("Build a supplier onboarding module with risk classification and manager approval.", "builder_ai"),
        ("Create an integration package allowing our customers' ERPs to send data.", "builder_ai"),
    ],
)
def test_route_question_matches_spec_examples(question, expected_agent):
    result = route_question(question)
    assert result["agent_key"] == expected_agent


@pytest.mark.django_db
def test_entitlement_grant_check_revoke(tenant_id):
    assert has_active_entitlement(tenant_id, "report_studio") is False
    grant_entitlement(tenant_id, "report_studio", plan_code="standard", granted_by="admin@cybercom.io")
    assert has_active_entitlement(tenant_id, "report_studio") is True
    revoke_entitlement(tenant_id, "report_studio")
    assert has_active_entitlement(tenant_id, "report_studio") is False


@pytest.mark.django_db
def test_agents_list_endpoint_reflects_entitlement(mint_token, mock_jwks, tenant_id):
    client = _client(mint_token, mock_jwks, tenant_id, "user-1")
    resp = client.get("/api/v1/cyai-platform/agents/")
    assert resp.status_code == 200
    by_key = {a["agent_key"]: a for a in resp.data}
    assert set(by_key) == {"ask_cycom", "report_studio", "builder_ai"}
    assert by_key["builder_ai"]["requires_elevated_approval"] is True

    grant_entitlement(tenant_id, "builder_ai")
    resp = client.get("/api/v1/cyai-platform/agents/")
    by_key = {a["agent_key"]: a for a in resp.data}
    assert by_key["builder_ai"]["entitled"] is True


@pytest.mark.django_db
def test_route_endpoint(mint_token, mock_jwks, tenant_id):
    client = _client(mint_token, mock_jwks, tenant_id, "user-1")
    resp = client.post(
        "/api/v1/cyai-platform/route/", {"question": "Build a customer credit approval workflow"}, format="json"
    )
    assert resp.status_code == 200
    assert resp.data["agent_key"] == "builder_ai"
    assert resp.data["requires_confirmation"] is True


@pytest.mark.django_db
def test_non_admin_cannot_manage_entitlements(mint_token, mock_jwks, tenant_id):
    client = _client(mint_token, mock_jwks, tenant_id, "user-1")
    agent = AgentDefinition.objects.get(agent_key="report_studio")
    resp = client.post(
        "/api/v1/cyai-platform/entitlements/",
        {"agent": str(agent.id), "plan_code": "standard"},
        format="json",
    )
    assert resp.status_code == 403


@pytest.mark.django_db
def test_platform_admin_can_manage_entitlements(mint_token, mock_jwks, tenant_id):
    client = _client(mint_token, mock_jwks, tenant_id, "admin-1", roles=["platform_admin"])
    agent = AgentDefinition.objects.get(agent_key="report_studio")
    resp = client.post(
        "/api/v1/cyai-platform/entitlements/",
        {"agent": str(agent.id), "plan_code": "standard"},
        format="json",
    )
    assert resp.status_code == 201
    assert AgentEntitlement.objects.filter(tenant_id=tenant_id, agent=agent, is_active=True).exists()
