"""
Bulk grade entry and bulk report-card publishing.

Marking is where a mis-keyed number does lasting damage — a score above the
maximum poisons every average a student appears in — so the batch is validated
as a whole and written all-or-nothing.
"""

import uuid
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from products.cyed.gradebook.models import Assessment, Grade
from products.cyed.reporting.models import ReportCard
from products.cyed.sis.models import ClassSection, Enrolment, Student


@pytest.fixture
def teacher_client(mint_token, mock_jwks, tenant_id):
    token = mint_token({
        "sub": str(uuid.uuid4()), "email": "teacher@cyed.edu.au",
        "tenant_id": str(tenant_id), "realm_access": {"roles": ["teacher"]},
    })
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


@pytest.fixture
def klass(tenant_id):
    section = ClassSection.objects.create(tenant_id=tenant_id, name="8A Mathematics", year_level=8)
    students = []
    for i, name in enumerate(["Ana", "Ben", "Cara", "Dev", "Eve"]):
        student = Student.objects.create(
            tenant_id=tenant_id, first_name=name, last_name=f"S{i}", year_level=8
        )
        Enrolment.objects.create(
            tenant_id=tenant_id, student=student, class_section=section, status="active"
        )
        students.append(student)
    return section, students


@pytest.fixture
def assessment(tenant_id, klass):
    section, _ = klass
    return Assessment.objects.create(
        tenant_id=tenant_id, class_section=section, name="Algebra Test",
        assessment_type="summative", max_score=Decimal("20"),
    )


def _grade(client, assessment, rows):
    return client.post(
        f"/api/v1/gradebook/assessments/{assessment.id}/bulk-grade/",
        {"grades": rows}, format="json",
    )


# ── the core promise ─────────────────────────────────────────────────────────
@pytest.mark.django_db
def test_one_request_marks_the_whole_set(teacher_client, tenant_id, klass, assessment):
    _, students = klass
    resp = _grade(teacher_client, assessment, [
        {"student": str(s.id), "score": 10 + i, "achievement_level": "B"}
        for i, s in enumerate(students)
    ])
    assert resp.status_code == 200, resp.data
    assert resp.data["created"] == 5
    assert resp.data["ungraded_remaining"] == 0
    assert Grade.objects.filter(tenant_id=tenant_id, assessment=assessment).count() == 5


@pytest.mark.django_db
def test_resubmitting_amends_rather_than_failing(teacher_client, klass, assessment):
    """Correcting one mark after handing back the papers is routine."""
    _, students = klass
    _grade(teacher_client, assessment, [{"student": str(students[0].id), "score": 12}])
    second = _grade(teacher_client, assessment, [{"student": str(students[0].id), "score": 15}])

    assert second.data["created"] == 0
    assert second.data["updated"] == 1
    assert Grade.objects.get(student=students[0]).score == Decimal("15")


@pytest.mark.django_db
def test_unchanged_rows_are_reported_as_such(teacher_client, klass, assessment):
    _, students = klass
    rows = [{"student": str(students[0].id), "score": 12}]
    _grade(teacher_client, assessment, rows)
    again = _grade(teacher_client, assessment, rows)
    assert again.data["unchanged"] == 1


@pytest.mark.django_db
def test_a_null_score_is_a_legitimate_ungraded_state(teacher_client, klass, assessment):
    _, students = klass
    resp = _grade(teacher_client, assessment, [
        {"student": str(students[0].id), "score": None, "comment": "Not submitted"},
    ])
    assert resp.status_code == 200
    assert Grade.objects.get(student=students[0]).score is None


# ── validation: the batch is all-or-nothing ──────────────────────────────────
@pytest.mark.django_db
def test_a_score_above_the_maximum_rejects_the_whole_batch(
    teacher_client, tenant_id, klass, assessment
):
    """
    95 entered against a test marked out of 20 is a 475% result that would
    poison every average that student appears in.
    """
    _, students = klass
    resp = _grade(teacher_client, assessment, [
        {"student": str(students[0].id), "score": 15},
        {"student": str(students[1].id), "score": 95},
    ])
    assert resp.status_code == 400
    assert "exceeds the maximum of 20" in resp.data["detail"]
    # Nothing written — a half-applied batch leaves a teacher guessing.
    assert Grade.objects.filter(tenant_id=tenant_id).count() == 0


@pytest.mark.django_db
def test_a_student_outside_the_class_rejects_the_batch(teacher_client, tenant_id, klass, assessment):
    _, students = klass
    stranger = Student.objects.create(
        tenant_id=tenant_id, first_name="Not", last_name="Here", year_level=9
    )
    resp = _grade(teacher_client, assessment, [
        {"student": str(students[0].id), "score": 10},
        {"student": str(stranger.id), "score": 10},
    ])
    assert resp.status_code == 400
    assert "not enrolled in the class" in resp.data["detail"]
    assert Grade.objects.filter(tenant_id=tenant_id).count() == 0


@pytest.mark.django_db
def test_unknown_achievement_level_is_refused(teacher_client, klass, assessment):
    _, students = klass
    resp = _grade(teacher_client, assessment, [
        {"student": str(students[0].id), "score": 10, "achievement_level": "A+"},
    ])
    assert resp.status_code == 400
    assert "is not an achievement level" in resp.data["detail"]


@pytest.mark.django_db
def test_duplicate_student_in_the_batch_is_refused(teacher_client, klass, assessment):
    _, students = klass
    resp = _grade(teacher_client, assessment, [
        {"student": str(students[0].id), "score": 10},
        {"student": str(students[0].id), "score": 18},
    ])
    assert resp.status_code == 400
    assert "appears twice" in resp.data["detail"]


@pytest.mark.django_db
def test_negative_score_is_refused(teacher_client, klass, assessment):
    _, students = klass
    resp = _grade(teacher_client, assessment, [{"student": str(students[0].id), "score": -1}])
    assert resp.status_code == 400


@pytest.mark.django_db
def test_empty_batch_is_refused(teacher_client, assessment):
    resp = _grade(teacher_client, assessment, [])
    assert resp.status_code == 400


# ── mark sheet ───────────────────────────────────────────────────────────────
@pytest.mark.django_db
def test_mark_sheet_shows_progress_through_the_pile(teacher_client, klass, assessment):
    _, students = klass
    _grade(teacher_client, assessment, [
        {"student": str(students[0].id), "score": 15},
        {"student": str(students[1].id), "score": 11},
    ])
    resp = teacher_client.get(f"/api/v1/gradebook/assessments/{assessment.id}/mark-sheet/")
    assert resp.status_code == 200
    assert resp.data["count"] == 5
    assert resp.data["graded"] == 2
    assert resp.data["max_score"] == "20.00"


# ── bulk report-card publish ─────────────────────────────────────────────────
@pytest.mark.django_db
def test_publish_class_issues_every_draft_report_in_one_request(
    teacher_client, tenant_id, klass
):
    section, students = klass
    for s in students:
        ReportCard.objects.create(
            tenant_id=tenant_id, student=s, term="Semester 1", status="draft"
        )

    resp = teacher_client.post(
        "/api/v1/reporting/report-cards/publish-class/",
        {"class_section": str(section.id), "term": "Semester 1"}, format="json",
    )
    assert resp.status_code == 200, resp.data
    assert resp.data["published"] == 5
    assert resp.data["failed"] == 0
    assert ReportCard.objects.filter(tenant_id=tenant_id, status="published").count() == 5
    # Every card gets its own tamper-evident document.
    assert all(r["content_hash"] for r in resp.data["results"])


@pytest.mark.django_db
def test_publish_class_leaves_already_published_reports_alone(teacher_client, tenant_id, klass):
    """
    Re-publishing mints a new version of a document families may already hold,
    so it has to be asked for explicitly.
    """
    section, students = klass
    for s in students:
        ReportCard.objects.create(tenant_id=tenant_id, student=s, term="Semester 1", status="draft")

    first = teacher_client.post(
        "/api/v1/reporting/report-cards/publish-class/",
        {"class_section": str(section.id)}, format="json",
    )
    assert first.data["published"] == 5

    second = teacher_client.post(
        "/api/v1/reporting/report-cards/publish-class/",
        {"class_section": str(section.id)}, format="json",
    )
    assert second.data["published"] == 0

    forced = teacher_client.post(
        "/api/v1/reporting/report-cards/publish-class/",
        {"class_section": str(section.id), "include_published": True}, format="json",
    )
    assert forced.data["published"] == 5
    assert forced.data["results"][0]["version"] == 2


@pytest.mark.django_db
def test_publish_class_reports_students_with_no_report_card(teacher_client, tenant_id, klass):
    """A teacher needs to know whether the whole class actually went out."""
    section, students = klass
    ReportCard.objects.create(
        tenant_id=tenant_id, student=students[0], term="Semester 1", status="draft"
    )
    resp = teacher_client.post(
        "/api/v1/reporting/report-cards/publish-class/",
        {"class_section": str(section.id)}, format="json",
    )
    assert resp.data["roster"] == 5
    assert resp.data["published"] == 1
    assert resp.data["without_report_card"] == 4


@pytest.mark.django_db
def test_publish_class_on_an_empty_section_is_refused(teacher_client, tenant_id):
    empty = ClassSection.objects.create(tenant_id=tenant_id, name="Ghost Class", year_level=9)
    resp = teacher_client.post(
        "/api/v1/reporting/report-cards/publish-class/",
        {"class_section": str(empty.id)}, format="json",
    )
    assert resp.status_code == 400
