"""
Assessment rubrics.

The property worth defending: the score is *derived* from the criteria. A
rubric whose total can disagree with the breakdown behind it is worse than no
rubric, because a student shown both stops trusting either.
"""

import uuid
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from products.cyed.gradebook.models import (
    Assessment,
    Grade,
    Rubric,
    RubricCriterion,
    RubricLevel,
    RubricMark,
)
from products.cyed.sis.models import ClassSection, Enrolment, Student


@pytest.fixture
def client_for(mint_token, mock_jwks, tenant_id):
    def _make(roles, email="teacher@cyed.edu.au"):
        c = APIClient()
        c.credentials(HTTP_AUTHORIZATION=f"Bearer {mint_token({
            'sub': str(uuid.uuid4()), 'email': email, 'tenant_id': str(tenant_id),
            'realm_access': {'roles': roles},
        })}")
        return c
    return _make


@pytest.fixture
def teacher(client_for):
    return client_for(["teacher"])


@pytest.fixture
def klass(tenant_id):
    section = ClassSection.objects.create(tenant_id=tenant_id, name="8A English", year_level=8)
    student = Student.objects.create(
        tenant_id=tenant_id, first_name="Mia", last_name="Tran", year_level=8,
        enrolment_status="enrolled",
    )
    Enrolment.objects.create(
        tenant_id=tenant_id, student=student, class_section=section, status="active"
    )
    return section, student


@pytest.fixture
def rubric(tenant_id):
    """Two criteria, three levels each. Structure is weighted double."""
    r = Rubric.objects.create(
        tenant_id=tenant_id, name="Extended response", subject="English", year_level=8
    )
    structure = RubricCriterion.objects.create(
        tenant_id=tenant_id, rubric=r, name="Structure", weight=Decimal("2"), sequence=1
    )
    evidence = RubricCriterion.objects.create(
        tenant_id=tenant_id, rubric=r, name="Use of evidence", weight=Decimal("1"), sequence=2
    )
    levels = {}
    for criterion in (structure, evidence):
        for label, marks, letter in [
            ("Excellent", 4, "A"), ("Sound", 2, "C"), ("Limited", 1, "E")
        ]:
            levels[(criterion.name, label)] = RubricLevel.objects.create(
                tenant_id=tenant_id, criterion=criterion, label=label, marks=Decimal(marks),
                achievement_level=letter,
                descriptor=f"{label} work on {criterion.name.lower()} — see exemplars.",
            )
    return r, structure, evidence, levels


@pytest.fixture
def assessment(tenant_id, klass, rubric):
    section, _student = klass
    r, *_ = rubric
    return Assessment.objects.create(
        tenant_id=tenant_id, class_section=section, name="Persuasive essay",
        assessment_type="summative", max_score=Decimal("12"), rubric=r,
    )


# ── the rubric itself ────────────────────────────────────────────────────────
@pytest.mark.django_db
def test_total_marks_accounts_for_weighting(rubric):
    r, *_ = rubric
    # Structure: best 4 × weight 2 = 8. Evidence: best 4 × weight 1 = 4.
    assert r.total_marks() == Decimal("12")


@pytest.mark.django_db
def test_a_level_needs_a_real_descriptor(teacher, tenant_id, rubric):
    """A level called "Good" with no description is a number in disguise."""
    _r, structure, *_ = rubric
    resp = teacher.post("/api/v1/gradebook/rubric-levels/", {
        "criterion": str(structure.id), "label": "Good", "descriptor": "Good", "marks": 3,
    }, format="json")
    assert resp.status_code == 400
    assert "what work at this level looks like" in str(resp.data).lower()


@pytest.mark.django_db
def test_two_levels_cannot_share_a_label_on_one_criterion(tenant_id, rubric):
    from django.db import IntegrityError

    _r, structure, *_ = rubric
    with pytest.raises(IntegrityError):
        RubricLevel.objects.create(
            tenant_id=tenant_id, criterion=structure, label="Sound", marks=Decimal("3"),
            descriptor="A second, conflicting definition of the same band.",
        )


# ── marking ──────────────────────────────────────────────────────────────────
@pytest.mark.django_db
def test_the_score_is_derived_from_the_criteria(teacher, tenant_id, klass, assessment, rubric):
    _section, student = klass
    _r, structure, evidence, levels = rubric

    resp = teacher.post(f"/api/v1/gradebook/assessments/{assessment.id}/rubric-mark/", {
        "student": str(student.id),
        "selections": {
            str(structure.id): str(levels[("Structure", "Excellent")].id),
            str(evidence.id): str(levels[("Use of evidence", "Sound")].id),
        },
    }, format="json")

    assert resp.status_code == 200, resp.data
    # Structure 4×2 = 8, evidence 2×1 = 2 → 10 of 12.
    assert Decimal(resp.data["earned"]) == Decimal("10")
    assert Decimal(resp.data["score"]) == Decimal("10")
    assert resp.data["complete"] is True


@pytest.mark.django_db
def test_the_score_scales_to_the_assessments_own_maximum(
    teacher, tenant_id, klass, assessment, rubric
):
    """A rubric out of 12 still reports sensibly on a task marked out of 100."""
    _section, student = klass
    _r, structure, evidence, levels = rubric
    assessment.max_score = Decimal("100")
    assessment.save(update_fields=["max_score"])

    teacher.post(f"/api/v1/gradebook/assessments/{assessment.id}/rubric-mark/", {
        "student": str(student.id),
        "selections": {
            str(structure.id): str(levels[("Structure", "Excellent")].id),
            str(evidence.id): str(levels[("Use of evidence", "Sound")].id),
        },
    }, format="json")

    grade = Grade.objects.get(assessment=assessment, student=student)
    assert grade.score == Decimal("83.33")   # 10/12 of 100


@pytest.mark.django_db
def test_partial_marking_is_allowed_and_reported(teacher, tenant_id, klass, assessment, rubric):
    """
    A teacher does one criterion for the whole class before starting the next;
    forcing a complete script before saving is how work gets lost.
    """
    _section, student = klass
    _r, structure, _evidence, levels = rubric

    resp = teacher.post(f"/api/v1/gradebook/assessments/{assessment.id}/rubric-mark/", {
        "student": str(student.id),
        "selections": {str(structure.id): str(levels[("Structure", "Sound")].id)},
    }, format="json")

    assert resp.data["complete"] is False
    assert resp.data["criteria_marked"] == 1
    assert resp.data["criteria_total"] == 2


@pytest.mark.django_db
def test_remarking_a_criterion_replaces_the_judgement(
    teacher, tenant_id, klass, assessment, rubric
):
    _section, student = klass
    _r, structure, _evidence, levels = rubric
    url = f"/api/v1/gradebook/assessments/{assessment.id}/rubric-mark/"

    teacher.post(url, {
        "student": str(student.id),
        "selections": {str(structure.id): str(levels[("Structure", "Limited")].id)},
    }, format="json")
    resp = teacher.post(url, {
        "student": str(student.id),
        "selections": {str(structure.id): str(levels[("Structure", "Excellent")].id)},
    }, format="json")

    assert RubricMark.objects.filter(criterion=structure).count() == 1
    assert Decimal(resp.data["earned"]) == Decimal("8")


@pytest.mark.django_db
def test_an_agreed_achievement_level_carries_up(teacher, tenant_id, klass, assessment, rubric):
    """A teacher should not re-judge A–E they have already implicitly given."""
    _section, student = klass
    _r, structure, evidence, levels = rubric

    resp = teacher.post(f"/api/v1/gradebook/assessments/{assessment.id}/rubric-mark/", {
        "student": str(student.id),
        "selections": {
            str(structure.id): str(levels[("Structure", "Excellent")].id),
            str(evidence.id): str(levels[("Use of evidence", "Excellent")].id),
        },
    }, format="json")
    assert resp.data["achievement_level"] == "A"


@pytest.mark.django_db
def test_mixed_levels_do_not_invent_an_overall_grade(
    teacher, tenant_id, klass, assessment, rubric
):
    """Averaging A and E into C is a judgement the rubric did not make."""
    _section, student = klass
    _r, structure, evidence, levels = rubric

    resp = teacher.post(f"/api/v1/gradebook/assessments/{assessment.id}/rubric-mark/", {
        "student": str(student.id),
        "selections": {
            str(structure.id): str(levels[("Structure", "Excellent")].id),
            str(evidence.id): str(levels[("Use of evidence", "Limited")].id),
        },
    }, format="json")
    assert resp.data["achievement_level"] == ""


@pytest.mark.django_db
def test_mixed_levels_clear_a_letter_typed_earlier(
    teacher, tenant_id, klass, assessment, rubric
):
    """
    A grade marked "D" by hand, then re-marked against the rubric to 15/16,
    must not keep the D. The letter was judged against a different score and
    now contradicts the one on screen.
    """
    _section, student = klass
    _r, structure, evidence, levels = rubric
    Grade.objects.create(
        tenant_id=tenant_id, assessment=assessment, student=student,
        score=Decimal("4"), achievement_level="D",
    )

    resp = teacher.post(f"/api/v1/gradebook/assessments/{assessment.id}/rubric-mark/", {
        "student": str(student.id),
        "selections": {
            str(structure.id): str(levels[("Structure", "Excellent")].id),
            str(evidence.id): str(levels[("Use of evidence", "Limited")].id),
        },
    }, format="json")
    assert resp.data["achievement_level"] == ""
    assert Grade.objects.get(assessment=assessment, student=student).achievement_level == ""


# ── refusals ─────────────────────────────────────────────────────────────────
@pytest.mark.django_db
def test_a_level_from_the_wrong_criterion_is_refused(
    teacher, tenant_id, klass, assessment, rubric
):
    """Catches the copy-paste error that scores against the wrong band."""
    _section, student = klass
    _r, structure, _evidence, levels = rubric

    resp = teacher.post(f"/api/v1/gradebook/assessments/{assessment.id}/rubric-mark/", {
        "student": str(student.id),
        # An "Use of evidence" level applied to the Structure criterion.
        "selections": {str(structure.id): str(levels[("Use of evidence", "Sound")].id)},
    }, format="json")
    assert resp.status_code == 400
    assert "is not a level on" in resp.data["detail"]


@pytest.mark.django_db
def test_marking_an_assessment_with_no_rubric_is_refused(teacher, tenant_id, klass):
    section, student = klass
    plain = Assessment.objects.create(
        tenant_id=tenant_id, class_section=section, name="Quick quiz",
        max_score=Decimal("10"),
    )
    resp = teacher.post(f"/api/v1/gradebook/assessments/{plain.id}/rubric-mark/", {
        "student": str(student.id), "selections": {"a": "b"},
    }, format="json")
    assert resp.status_code == 400
    assert "no rubric" in resp.data["detail"]


@pytest.mark.django_db
def test_empty_selections_are_refused(teacher, klass, assessment):
    _section, student = klass
    resp = teacher.post(f"/api/v1/gradebook/assessments/{assessment.id}/rubric-mark/", {
        "student": str(student.id), "selections": {},
    }, format="json")
    assert resp.status_code == 400


# ── the feedback a student reads ─────────────────────────────────────────────
@pytest.mark.django_db
def test_the_breakdown_is_available_on_the_grade(
    teacher, tenant_id, klass, assessment, rubric
):
    """The breakdown *is* the feedback — it is what tells a student what to fix."""
    _section, student = klass
    _r, structure, evidence, levels = rubric
    teacher.post(f"/api/v1/gradebook/assessments/{assessment.id}/rubric-mark/", {
        "student": str(student.id),
        "selections": {
            str(structure.id): str(levels[("Structure", "Sound")].id),
            str(evidence.id): str(levels[("Use of evidence", "Excellent")].id),
        },
    }, format="json")

    grade = Grade.objects.get(assessment=assessment, student=student)
    resp = teacher.get(f"/api/v1/gradebook/grades/{grade.id}/")
    marks = {m["criterion_name"]: m for m in resp.data["rubric_marks"]}

    assert marks["Structure"]["level_label"] == "Sound"
    assert marks["Use of evidence"]["level_label"] == "Excellent"
    assert marks["Structure"]["descriptor"]


@pytest.mark.django_db
def test_rubrics_are_reusable_across_assessments(tenant_id, klass, rubric):
    """A school's "Extended response" rubric is the same one every term."""
    section, _student = klass
    r, *_ = rubric
    for name in ("Essay 1", "Essay 2"):
        Assessment.objects.create(
            tenant_id=tenant_id, class_section=section, name=name,
            max_score=Decimal("12"), rubric=r,
        )
    assert r.assessments.count() == 2
