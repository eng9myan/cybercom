import uuid

import pytest
from rest_framework.test import APIClient

from products.cyed.ai_agents.models import AgentDefinition, GeneratedArtifact
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
def teacher_agents(tenant_id):
    for key, cap in [("cyed.lesson_planner", "lesson_planner"),
                     ("cyed.rubric", "rubric"),
                     ("cyed.differentiator", "differentiator")]:
        AgentDefinition.objects.create(tenant_id=tenant_id, key=key, name=key, capability=cap)


# ── Lesson planner + HITL ────────────────────────────────────────────────────
@pytest.mark.django_db
def test_lesson_plan_generates_pending_then_approves(platform_admin_client, tenant_id, acara, teacher_agents):
    resp = platform_admin_client.post(
        "/api/v1/ai/lesson-planner/generate/",
        {"topic": "irrational numbers", "year_level": 8},
        format="json",
    )
    assert resp.status_code == 201, resp.data
    assert resp.data["artifact_type"] == "lesson_plan"
    assert resp.data["status"] == "pending_review"  # HITL
    assert "AC9M8N01" in resp.data["curriculum_codes"]
    assert resp.data["content"]["learning_objectives"]
    artifact_id = resp.data["id"]

    # Shows up in the pending HITL queue.
    queue = platform_admin_client.get("/api/v1/ai/artifacts/?status=pending_review&artifact_type=lesson_plan")
    rows = queue.data["results"] if isinstance(queue.data, dict) else queue.data
    assert any(r["id"] == artifact_id for r in rows)

    # Teacher approves.
    appr = platform_admin_client.post(f"/api/v1/ai/artifacts/{artifact_id}/approve/", {"note": "Good"}, format="json")
    assert appr.status_code == 200
    assert appr.data["status"] == "approved"
    assert appr.data["reviewed_by"] == "teacher@cyed.edu.au"


@pytest.mark.django_db
def test_lesson_plan_refuses_without_grounding(platform_admin_client, tenant_id, teacher_agents):
    resp = platform_admin_client.post(
        "/api/v1/ai/lesson-planner/generate/",
        {"topic": "quidditch tactics", "year_level": 8},
        format="json",
    )
    assert resp.status_code == 400


@pytest.mark.django_db
def test_generate_fails_when_agent_not_provisioned(platform_admin_client, tenant_id, acara):
    resp = platform_admin_client.post(
        "/api/v1/ai/lesson-planner/generate/",
        {"topic": "irrational numbers", "year_level": 8},
        format="json",
    )
    assert resp.status_code == 400  # agent not provisioned


# ── Rubric ───────────────────────────────────────────────────────────────────
@pytest.mark.django_db
def test_rubric_has_ae_levels(platform_admin_client, tenant_id, acara, teacher_agents):
    resp = platform_admin_client.post(
        "/api/v1/ai/rubric/generate/",
        {"assessment_title": "irrational numbers test", "year_level": 8},
        format="json",
    )
    assert resp.status_code == 201, resp.data
    assert resp.data["artifact_type"] == "rubric"
    criteria = resp.data["content"]["criteria"]
    assert len(criteria) >= 1
    assert set(criteria[0]["levels"].keys()) == {"A", "B", "C", "D", "E"}


# ── Differentiator + learner profile ─────────────────────────────────────────
@pytest.mark.django_db
def test_differentiator_adapts_to_profile(platform_admin_client, tenant_id, acara, teacher_agents):
    student = Student.objects.create(tenant_id=tenant_id, first_name="Minh", last_name="Nguyen", year_level=8)
    LearnerProfile.objects.create(
        tenant_id=tenant_id, student=student, eald_level="DV", first_language="Vietnamese",
        is_neurodivergent=True,
    )
    resp = platform_admin_client.post(
        "/api/v1/ai/differentiator/generate/",
        {"topic": "irrational numbers", "year_level": 8, "student": str(student.id)},
        format="json",
    )
    assert resp.status_code == 201, resp.data
    content = resp.data["content"]
    assert set(content["tiers"].keys()) == {"support", "core", "extension"}
    assert "eald:DV" in content["applied_adaptations"]
    assert "chunked" in content["applied_adaptations"]


# ── Integrity (process-provenance, human decision) ───────────────────────────
@pytest.mark.django_db
def test_integrity_high_risk_flag_then_human_decides(platform_admin_client, tenant_id):
    resp = platform_admin_client.post(
        "/api/v1/ai/integrity/reviews/",
        {"title": "Essay 1", "draft_versions": 1, "edit_span_minutes": 2,
         "paste_events": 6, "large_paste_events": 2, "disclosed_ai_use": False},
        format="json",
    )
    assert resp.status_code == 201, resp.data
    assert resp.data["risk_band"] == "high"
    assert resp.data["decision"] == "pending"  # never auto-accuses
    assert resp.data["signals"]["advisory_only"]
    review_id = resp.data["id"]

    decided = platform_admin_client.post(
        f"/api/v1/ai/integrity/reviews/{review_id}/decide/",
        {"decision": "cleared", "note": "Spoke with student; legitimate."},
        format="json",
    )
    assert decided.status_code == 200
    assert decided.data["decision"] == "cleared"
    assert decided.data["decided_by"] == "teacher@cyed.edu.au"


@pytest.mark.django_db
def test_integrity_disclosure_lowers_band(platform_admin_client, tenant_id):
    resp = platform_admin_client.post(
        "/api/v1/ai/integrity/reviews/",
        {"title": "Essay 2", "draft_versions": 1, "edit_span_minutes": 2,
         "paste_events": 6, "large_paste_events": 2, "disclosed_ai_use": True,
         "ai_disclosure_note": "Used AI to brainstorm, then wrote it myself."},
        format="json",
    )
    assert resp.status_code == 201, resp.data
    # Same signals as the high-risk case, but disclosure caps it at medium + notes it.
    assert resp.data["risk_band"] == "medium"
    assert "ai_disclosed" in resp.data["signals"]


@pytest.mark.django_db
def test_integrity_clean_process_is_low_risk(platform_admin_client, tenant_id):
    resp = platform_admin_client.post(
        "/api/v1/ai/integrity/reviews/",
        {"title": "Essay 3", "draft_versions": 8, "edit_span_minutes": 240,
         "paste_events": 0, "large_paste_events": 0, "disclosed_ai_use": False},
        format="json",
    )
    assert resp.status_code == 201, resp.data
    assert resp.data["risk_band"] == "low"
