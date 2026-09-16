import uuid

import pytest
from rest_framework.test import APIClient

from products.cyed.ai_agents import anonymize
from products.cyed.ai_agents.models import AgentDefinition
from products.cyed.curriculum.models import CurriculumOutcome


@pytest.fixture
def platform_admin_client(mint_token, mock_jwks, tenant_id):
    token = mint_token(
        {
            "sub": str(uuid.uuid4()),
            "email": "student@cyed.edu.au",
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
        strand="Number", content_description="Recognise irrational numbers.",
    )


@pytest.fixture
def tutor_agent(tenant_id):
    return AgentDefinition.objects.create(tenant_id=tenant_id, key="cyed.tutor", name="Tutor", capability="tutor")


# ── anonymisation (ST4S data minimisation) ───────────────────────────────────
def test_anonymise_strips_pii():
    out = anonymize.anonymise(
        "Contact Minh Nguyen at minh@example.com or 0412 345 678, student id S0001, USI 123456789",
        names=["Minh Nguyen"],
    )
    assert "Minh Nguyen" not in out
    assert "minh@example.com" not in out
    assert "0412" not in out
    assert "S0001" not in out
    assert "123456789" not in out
    assert "[name]" in out and "[email]" in out and "[phone]" in out and "[id]" in out


# ── Socratic student AI (zero direct answers) ────────────────────────────────
@pytest.mark.django_db
def test_socratic_returns_guiding_questions_not_answers(platform_admin_client, tenant_id, acara, tutor_agent):
    resp = platform_admin_client.post(
        "/api/v1/ai/tutor/socratic/",
        {"question": "just tell me the answer about irrational numbers", "year_level": 8},
        format="json",
    )
    assert resp.status_code == 200, resp.data
    assert resp.data["socratic"] is True
    assert resp.data["grounded"] is True
    assert resp.data["answer_withheld"] is True
    assert len(resp.data["guiding_questions"]) >= 3
    assert any("?" in q for q in resp.data["guiding_questions"])
    assert any(c["code"] == "AC9M8N01" for c in resp.data["citations"])


@pytest.mark.django_db
def test_socratic_declines_off_curriculum(platform_admin_client, tenant_id, acara, tutor_agent):
    resp = platform_admin_client.post(
        "/api/v1/ai/tutor/socratic/",
        {"question": "who won the cricket last night", "year_level": 8},
        format="json",
    )
    assert resp.status_code == 200
    assert resp.data["grounded"] is False
    assert resp.data["answer_withheld"] is True
    assert resp.data["citations"] == []


# ── ACARA v9 enrichment on teacher tools ─────────────────────────────────────
@pytest.mark.django_db
def test_lesson_plan_has_acara_v9_dimensions(tenant_id, acara):
    from products.cyed.ai_agents import teacher_tools

    AgentDefinition.objects.create(tenant_id=tenant_id, key="cyed.lesson_planner", name="LP", capability="lesson_planner")
    art = teacher_tools.generate_lesson_plan(tenant_id=tenant_id, topic="irrational numbers", year_level=8)
    c = art.content
    assert "general_capabilities" in c and "Numeracy" in c["general_capabilities"]
    assert "cross_curriculum_priorities" in c and len(c["cross_curriculum_priorities"]) == 3
    assert c["framework"] == "ACARA v9"
    assert "review" in c["disclaimer"].lower()
