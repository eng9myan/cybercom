import uuid
from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from products.cyed.assessment.models import Assignment, Submission
from products.cyed.gradebook.models import Assessment, Grade
from products.cyed.learning_bridge.models import FamilyResource, OfflineActivityPack
from products.cyed.sis.models import ClassSection, Enrolment, Guardian, Student


@pytest.fixture
def client_for(mint_token, mock_jwks, tenant_id):
    def _make(roles, email="parent@cyed.edu.au"):
        c = APIClient()
        c.credentials(HTTP_AUTHORIZATION=f"Bearer {mint_token({
            'sub': str(uuid.uuid4()), 'email': email, 'tenant_id': str(tenant_id),
            'realm_access': {'roles': roles},
        })}")
        return c
    return _make


@pytest.fixture
def section(tenant_id):
    return ClassSection.objects.create(tenant_id=tenant_id, name="8A Maths", year_level=8)


@pytest.fixture
def student(tenant_id, section):
    s = Student.objects.create(
        tenant_id=tenant_id, first_name="Mia", last_name="Tran", year_level=8,
        enrolment_status="enrolled", language_at_home="Vietnamese",
    )
    Enrolment.objects.create(tenant_id=tenant_id, student=s, class_section=section, status="active")
    return s


@pytest.fixture
def parent_client(client_for, tenant_id, student):
    Guardian.objects.create(
        tenant_id=tenant_id, first_name="Lan", last_name="Tran", email="parent@cyed.edu.au",
    ).students.add(student)
    return client_for(["parent"])


@pytest.mark.django_db
def test_missed_and_upcoming_assignments_split_correctly(tenant_id, section, student):
    from products.cyed.learning_bridge.services import bridge_summary

    now = timezone.now()
    overdue = Assignment.objects.create(
        tenant_id=tenant_id, class_section=section, title="Overdue essay",
        due_at=now - timedelta(days=2), is_published=True,
    )
    soon = Assignment.objects.create(
        tenant_id=tenant_id, class_section=section, title="Due soon quiz",
        due_at=now + timedelta(days=5), is_published=True,
    )
    far_off = Assignment.objects.create(
        tenant_id=tenant_id, class_section=section, title="Term project",
        due_at=now + timedelta(days=60), is_published=True,
    )
    already_done = Assignment.objects.create(
        tenant_id=tenant_id, class_section=section, title="Handed in already",
        due_at=now - timedelta(days=1), is_published=True,
    )
    Submission.objects.create(
        tenant_id=tenant_id, assignment=already_done, student=student, status=Submission.SUBMITTED,
    )

    summary = bridge_summary(tenant_id, student)
    missed_titles = {r["title"] for r in summary["missed_assignments"]}
    upcoming_titles = {r["title"] for r in summary["upcoming_assignments"]}

    assert missed_titles == {"Overdue essay"}
    assert upcoming_titles == {"Due soon quiz"}
    assert "Term project" not in missed_titles | upcoming_titles
    assert "Handed in already" not in missed_titles | upcoming_titles


@pytest.mark.django_db
def test_learning_progress_carries_curriculum_code(tenant_id, section, student):
    from products.cyed.learning_bridge.services import bridge_summary

    assessment = Assessment.objects.create(
        tenant_id=tenant_id, class_section=section, name="Fractions test",
        curriculum_code="AC9M8N01", max_score=50,
    )
    Grade.objects.create(
        tenant_id=tenant_id, assessment=assessment, student=student,
        score=42, achievement_level="B",
    )
    summary = bridge_summary(tenant_id, student)
    assert len(summary["learning_progress"]) == 1
    row = summary["learning_progress"][0]
    assert row["curriculum_code"] == "AC9M8N01"
    assert row["achievement_level"] == "B"
    assert row["score"] == "42.00"


@pytest.mark.django_db
def test_resources_scoped_by_year_level_and_ranked_by_language(tenant_id, student):
    from products.cyed.learning_bridge.services import bridge_summary

    FamilyResource.objects.create(
        tenant_id=tenant_id, title="English resource", is_published=True,
        year_level_min=0, year_level_max=12,
    )
    FamilyResource.objects.create(
        tenant_id=tenant_id, title="Vietnamese resource", is_published=True,
        year_level_min=0, year_level_max=12, language="Vietnamese",
    )
    FamilyResource.objects.create(
        tenant_id=tenant_id, title="Wrong year level", is_published=True,
        year_level_min=0, year_level_max=3,
    )
    FamilyResource.objects.create(
        tenant_id=tenant_id, title="Unpublished draft", is_published=False,
        year_level_min=0, year_level_max=12,
    )

    summary = bridge_summary(tenant_id, student)
    titles = [r.title for r in summary["resources"]]
    assert "Wrong year level" not in titles
    assert "Unpublished draft" not in titles
    assert titles[0] == "Vietnamese resource"  # language match ranked first


@pytest.mark.django_db
def test_offline_packs_scoped_by_year_level(tenant_id, student):
    from products.cyed.learning_bridge.services import bridge_summary

    OfflineActivityPack.objects.create(
        tenant_id=tenant_id, title="Y8 maths pack", is_published=True,
        year_level_min=7, year_level_max=9,
    )
    OfflineActivityPack.objects.create(
        tenant_id=tenant_id, title="Primary pack", is_published=True,
        year_level_min=0, year_level_max=6,
    )
    summary = bridge_summary(tenant_id, student)
    titles = [p.title for p in summary["offline_packs"]]
    assert titles == ["Y8 maths pack"]


@pytest.mark.django_db
def test_summary_endpoint_scopes_to_parents_own_child(parent_client, tenant_id):
    resp = parent_client.get("/api/v1/learning-bridge/summary/")
    assert resp.status_code == 200
    assert resp.data["student_name"] == "Mia Tran"


@pytest.mark.django_db
def test_summary_endpoint_refuses_a_students_data_to_the_wrong_parent(tenant_id, section, client_for):
    other_student = Student.objects.create(
        tenant_id=tenant_id, first_name="Not", last_name="Mine", year_level=8,
        enrolment_status="enrolled",
    )
    parent = client_for(["parent"], email="stranger@cyed.edu.au")
    resp = parent.get(f"/api/v1/learning-bridge/summary/?student={other_student.id}")
    # Either "not linked to any child" (404) or "linked to a different child,
    # this one isn't it" (403) — never a 200 with someone else's data.
    assert resp.status_code in (403, 404)


@pytest.mark.django_db
def test_summary_endpoint_staff_must_specify_a_student(tenant_id, client_for):
    staff = client_for(["tenant_admin"], email="staff@cyed.edu.au")
    resp = staff.get("/api/v1/learning-bridge/summary/")
    assert resp.status_code == 400


@pytest.mark.django_db
def test_only_staff_may_write_resources(tenant_id, client_for):
    staff = client_for(["tenant_admin"], email="staff@cyed.edu.au")
    resp = staff.post("/api/v1/learning-bridge/resources/", {
        "title": "New resource", "year_level_min": 0, "year_level_max": 12,
    }, format="json")
    assert resp.status_code == 201, resp.data
    assert resp.data["created_by"] == "staff@cyed.edu.au"

    parent = client_for(["parent"], email="parent2@cyed.edu.au")
    denied = parent.post("/api/v1/learning-bridge/resources/", {
        "title": "Should fail", "year_level_min": 0, "year_level_max": 12,
    }, format="json")
    assert denied.status_code == 403


@pytest.mark.django_db
def test_approve_action_publishes_pack_and_records_approver(tenant_id, client_for):
    pack = OfflineActivityPack.objects.create(
        tenant_id=tenant_id, title="Draft pack", is_published=False,
        year_level_min=0, year_level_max=12,
    )
    staff = client_for(["tenant_admin"], email="teacher@cyed.edu.au")
    resp = staff.post(f"/api/v1/learning-bridge/offline-packs/{pack.id}/approve/")
    assert resp.status_code == 200
    assert resp.data["is_published"] is True
    assert resp.data["approved_by"] == "teacher@cyed.edu.au"
