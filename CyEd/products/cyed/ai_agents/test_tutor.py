import uuid

import pytest
from rest_framework.test import APIClient

from products.cyed.ai_agents.models import AgentDefinition, AgentInteractionLog
from products.cyed.curriculum.models import CurriculumOutcome
from products.cyed.sis.models import Student
from products.cyed.wellbeing.models import LearnerProfile


@pytest.fixture
def platform_admin_client(mint_token, mock_jwks, tenant_id):
    token = mint_token(
        {
            "sub": str(uuid.uuid4()),
            "email": "teacher@cyed.edu.au",
            "tenant_id": str(tenant_id),
            "realm_access": {"roles": ["platform_admin"]},
        }
    )
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


@pytest.fixture
def acara(tenant_id):
    return CurriculumOutcome.objects.create(
        tenant_id=tenant_id, code="AC9M8N01", learning_area="Mathematics", year_level=8,
        strand="Number", content_description="Recognise irrational numbers and their place on the number line.",
    )


@pytest.fixture
def tutor_agent(tenant_id):
    return AgentDefinition.objects.create(
        tenant_id=tenant_id, key="cyed.tutor", name="Tutor", capability="tutor", grounding="ACARA"
    )


@pytest.mark.django_db
def test_grounded_answer_with_citations_and_log(platform_admin_client, tenant_id, acara, tutor_agent):
    resp = platform_admin_client.post(
        "/api/v1/ai/tutor/ask/",
        {"question": "Can you explain irrational numbers?", "year_level": 8},
        format="json",
    )
    assert resp.status_code == 200, resp.data
    assert resp.data["grounded"] is True
    assert any(c["code"] == "AC9M8N01" for c in resp.data["citations"])
    assert "AC9M8N01" in resp.data["answer"]
    assert resp.data["reviewed_by_human"] is False
    # Transparency log written.
    assert AgentInteractionLog.objects.filter(
        tenant_id=tenant_id, agent=tutor_agent, curriculum_code="AC9M8N01"
    ).count() == 1


@pytest.mark.django_db
def test_out_of_curriculum_is_declined(platform_admin_client, tenant_id, acara, tutor_agent):
    resp = platform_admin_client.post(
        "/api/v1/ai/tutor/ask/",
        {"question": "Who won the football grand final?", "year_level": 8},
        format="json",
    )
    assert resp.status_code == 200
    assert resp.data["grounded"] is False
    assert resp.data["citations"] == []
    assert "curriculum" in resp.data["answer"].lower()


@pytest.mark.django_db
def test_code_lookup_short_circuits(platform_admin_client, tenant_id, acara, tutor_agent):
    resp = platform_admin_client.post(
        "/api/v1/ai/tutor/ask/",
        {"question": "Tell me about AC9M8N01"},
        format="json",
    )
    assert resp.status_code == 200
    assert resp.data["grounded"] is True
    assert resp.data["citations"][0]["code"] == "AC9M8N01"


@pytest.mark.django_db
def test_adapts_to_eald_learner_profile(platform_admin_client, tenant_id, acara, tutor_agent):
    student = Student.objects.create(tenant_id=tenant_id, first_name="Minh", last_name="Nguyen", year_level=8)
    LearnerProfile.objects.create(
        tenant_id=tenant_id, student=student, eald_level="DV", first_language="Vietnamese", is_neurodivergent=True
    )
    # AI operating on a named student requires recorded consent (governance).
    from products.cyed.governance.models import ConsentRecord
    ConsentRecord.objects.create(tenant_id=tenant_id, student=student, consent_type="ai_use", granted=True)

    resp = platform_admin_client.post(
        "/api/v1/ai/tutor/ask/",
        {"question": "Explain irrational numbers", "year_level": 8, "student": str(student.id)},
        format="json",
    )
    assert resp.status_code == 200
    assert "eald:DV" in resp.data["adaptations"]
    assert "chunked" in resp.data["adaptations"]
    assert "first_language:Vietnamese" in resp.data["adaptations"]


@pytest.mark.django_db
def test_missing_question_rejected(platform_admin_client, tenant_id):
    resp = platform_admin_client.post("/api/v1/ai/tutor/ask/", {"year_level": 8}, format="json")
    assert resp.status_code == 400
