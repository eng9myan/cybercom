import uuid

import pytest
from rest_framework.test import APIClient

from products.cyed.ai_agents.models import AgentDefinition


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
def test_register_tutor_agent_privacy_defaults(platform_admin_client, tenant_id):
    resp = platform_admin_client.post(
        "/api/v1/ai/agents/",
        {"key": "cyed.tutor", "name": "Curriculum Tutor", "capability": "tutor",
         "grounding": "ACARA"},
        format="json",
    )
    assert resp.status_code == 201, resp.data
    # Privacy-first defaults must hold without being explicitly set.
    assert resp.data["no_train"] is True
    assert resp.data["data_residency"] == "AU"


@pytest.mark.django_db
def test_agent_key_unique_per_tenant(platform_admin_client, tenant_id):
    AgentDefinition.objects.create(tenant_id=tenant_id, key="cyed.tutor", name="Tutor")
    dup = platform_admin_client.post(
        "/api/v1/ai/agents/",
        {"key": "cyed.tutor", "name": "Tutor 2", "capability": "tutor"},
        format="json",
    )
    assert dup.status_code == 400


@pytest.mark.django_db
def test_seed_command_provisions_school_and_agents(tenant_id):
    from django.core.management import call_command

    call_command("seed_cyed_demo", tenant=str(tenant_id))

    from products.cyed.sis.models import Enrolment, Student

    assert Student.objects.filter(tenant_id=tenant_id).count() == 1
    assert Enrolment.objects.filter(tenant_id=tenant_id).count() == 1
    assert AgentDefinition.objects.filter(tenant_id=tenant_id, key="cyed.tutor").exists()
    assert AgentDefinition.objects.filter(tenant_id=tenant_id).count() == 5

    # Idempotent — second run creates no duplicates.
    call_command("seed_cyed_demo", tenant=str(tenant_id))
    assert Student.objects.filter(tenant_id=tenant_id).count() == 1
    assert AgentDefinition.objects.filter(tenant_id=tenant_id).count() == 5
