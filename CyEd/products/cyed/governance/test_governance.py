import uuid

import pytest
from rest_framework.test import APIClient

from products.cyed.governance.models import AuditEvent, ConsentRecord
from products.cyed.sis.models import Guardian, Student


@pytest.fixture
def client_for(mint_token, mock_jwks, tenant_id):
    """Build an authenticated client with given roles + email for this tenant."""
    def _make(roles, email="user@cyed.edu.au"):
        token = mint_token(
            {
                "sub": str(uuid.uuid4()),
                "email": email,
                "tenant_id": str(tenant_id),
                "realm_access": {"roles": roles},
            }
        )
        c = APIClient()
        c.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        return c
    return _make


# ── RBAC object scoping ──────────────────────────────────────────────────────
@pytest.mark.django_db
def test_parent_sees_only_own_child(client_for, tenant_id):
    mine = Student.objects.create(tenant_id=tenant_id, first_name="Ivy", last_name="Chen", year_level=8)
    other = Student.objects.create(tenant_id=tenant_id, first_name="Sam", last_name="Other", year_level=8)
    guardian = Guardian.objects.create(tenant_id=tenant_id, first_name="Jia", last_name="Chen",
                                       email="parent@home.com")
    guardian.students.add(mine)

    parent = client_for(["parent"], email="parent@home.com")
    resp = parent.get("/api/v1/sis/students/")
    rows = resp.data["results"] if isinstance(resp.data, dict) else resp.data
    ids = {r["id"] for r in rows}
    assert str(mine.id) in ids
    assert str(other.id) not in ids


@pytest.mark.django_db
def test_student_sees_only_self(client_for, tenant_id):
    me = Student.objects.create(tenant_id=tenant_id, first_name="Ava", last_name="Lee", year_level=9,
                                email="ava@student.cyed.edu.au")
    Student.objects.create(tenant_id=tenant_id, first_name="Ben", last_name="Ng", year_level=9)

    student = client_for(["student"], email="ava@student.cyed.edu.au")
    resp = student.get("/api/v1/sis/students/")
    rows = resp.data["results"] if isinstance(resp.data, dict) else resp.data
    assert len(rows) == 1
    assert rows[0]["id"] == str(me.id)


@pytest.mark.django_db
def test_teacher_sees_all_students(client_for, tenant_id):
    Student.objects.create(tenant_id=tenant_id, first_name="A", last_name="One", year_level=7)
    Student.objects.create(tenant_id=tenant_id, first_name="B", last_name="Two", year_level=7)
    teacher = client_for(["teacher"])
    resp = teacher.get("/api/v1/sis/students/")
    rows = resp.data["results"] if isinstance(resp.data, dict) else resp.data
    assert len(rows) == 2


@pytest.mark.django_db
def test_parent_cannot_write_students(client_for, tenant_id):
    parent = client_for(["parent"], email="p@home.com")
    resp = parent.post("/api/v1/sis/students/", {"first_name": "X", "last_name": "Y"}, format="json")
    assert resp.status_code == 403


# ── Confidential wellbeing + at-risk restricted ──────────────────────────────
@pytest.mark.django_db
def test_teacher_blocked_from_confidential_notes(client_for, tenant_id):
    teacher = client_for(["teacher"])
    assert teacher.get("/api/v1/wellbeing/notes/").status_code == 403
    pastoral = client_for(["counsellor"])
    assert pastoral.get("/api/v1/wellbeing/notes/").status_code == 200


@pytest.mark.django_db
def test_teacher_blocked_from_at_risk(client_for, tenant_id):
    teacher = client_for(["teacher"])
    assert teacher.get("/api/v1/analytics/at-risk/").status_code == 403
    leadership = client_for(["principal"])
    assert leadership.get("/api/v1/analytics/at-risk/").status_code == 200


# ── Consent gate on AI ───────────────────────────────────────────────────────
@pytest.mark.django_db
def test_ai_blocked_without_consent_allowed_with(client_for, tenant_id):
    from products.cyed.ai_agents.models import AgentDefinition
    from products.cyed.curriculum.models import CurriculumOutcome

    AgentDefinition.objects.create(tenant_id=tenant_id, key="cyed.tutor", name="Tutor", capability="tutor")
    CurriculumOutcome.objects.create(tenant_id=tenant_id, code="AC9M8N01", learning_area="Mathematics",
                                     year_level=8, content_description="Recognise irrational numbers.")
    student = Student.objects.create(tenant_id=tenant_id, first_name="Minh", last_name="Nguyen", year_level=8)
    teacher = client_for(["teacher"])

    denied = teacher.post("/api/v1/ai/tutor/ask/",
                          {"question": "explain irrational numbers", "year_level": 8, "student": str(student.id)},
                          format="json")
    assert denied.status_code == 403

    ConsentRecord.objects.create(tenant_id=tenant_id, student=student, consent_type="ai_use", granted=True)
    allowed = teacher.post("/api/v1/ai/tutor/ask/",
                           {"question": "explain irrational numbers", "year_level": 8, "student": str(student.id)},
                           format="json")
    assert allowed.status_code == 200


# ── Immutable audit ──────────────────────────────────────────────────────────
@pytest.mark.django_db
def test_student_write_is_audited_and_log_is_read_only(client_for, tenant_id):
    admin = client_for(["tenant_admin"])
    created = admin.post("/api/v1/sis/students/", {"first_name": "Zoe", "last_name": "Kidd", "year_level": 8},
                         format="json")
    assert created.status_code == 201
    sid = created.data["id"]
    assert AuditEvent.objects.filter(tenant_id=tenant_id, action="create",
                                     model_label="cyed_sis.Student", object_id=sid).exists()

    # Audit log is staff-readable but append-only (no create endpoint).
    assert admin.get("/api/v1/governance/audit-events/").status_code == 200
    assert admin.post("/api/v1/governance/audit-events/", {}, format="json").status_code == 405


@pytest.mark.django_db
def test_audit_log_not_visible_to_parents(client_for, tenant_id):
    parent = client_for(["parent"], email="p@home.com")
    assert parent.get("/api/v1/governance/audit-events/").status_code == 403
