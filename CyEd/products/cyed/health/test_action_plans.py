"""
Medical action plans.

The document a teacher needs in ninety seconds, on a phone, possibly in a car
park. These tests guard the properties that make it usable at that moment:
readable by any staff member, never silently hidden because the paperwork
lapsed, and never storing "this child needs an EpiPen" without saying where it is.
"""

import uuid
from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from products.cyed.health.models import ActionPlan
from products.cyed.sis.models import ClassSection, Enrolment, Student

TODAY = timezone.localdate()


@pytest.fixture
def client_for(mint_token, mock_jwks, tenant_id):
    def _make(roles, email="nurse@cyed.edu.au"):
        c = APIClient()
        c.credentials(HTTP_AUTHORIZATION=f"Bearer {mint_token({
            'sub': str(uuid.uuid4()), 'email': email, 'tenant_id': str(tenant_id),
            'realm_access': {'roles': roles},
        })}")
        return c
    return _make


@pytest.fixture
def nurse(client_for):
    return client_for(["pastoral"])


@pytest.fixture
def students(tenant_id):
    return [
        Student.objects.create(
            tenant_id=tenant_id, first_name=n, last_name="Tran",
            year_level=8, enrolment_status="enrolled",
        )
        for n in ["Ana", "Ben", "Cara"]
    ]


def _plan(tenant_id, student, **extra):
    body = {
        "tenant_id": tenant_id,
        "student": student,
        "plan_type": "anaphylaxis",
        "severity": "critical",
        "triggers": "Peanuts, tree nuts",
        "emergency_steps": "1. Lay flat. 2. EpiPen to outer thigh. 3. Call 000.",
        "medication": "EpiPen Jr 150mcg",
        "medication_location": "Front office, red box",
        "review_due": TODAY + timedelta(days=300),
    }
    body.update(extra)
    return ActionPlan.objects.create(**body)


# ── status and expiry ────────────────────────────────────────────────────────
@pytest.mark.django_db
def test_a_reviewed_plan_is_current(tenant_id, students):
    plan = _plan(tenant_id, students[0])
    assert plan.status(TODAY) == "current"
    assert plan.is_current(TODAY)


@pytest.mark.django_db
def test_a_plan_past_its_review_date_is_expired(tenant_id, students):
    """An out-of-date plan may describe the wrong dose."""
    plan = _plan(tenant_id, students[0], review_due=TODAY - timedelta(days=1))
    assert plan.status(TODAY) == "expired"


@pytest.mark.django_db
def test_a_plan_nearing_review_is_flagged_but_still_usable(tenant_id, students):
    """Sixty days is roughly how long a GP appointment takes to get."""
    plan = _plan(tenant_id, students[0], review_due=TODAY + timedelta(days=20))
    assert plan.status(TODAY) == "due_for_review"
    assert plan.is_current(TODAY) is True


@pytest.mark.django_db
def test_a_plan_with_no_review_date_is_still_usable(tenant_id, students):
    plan = _plan(tenant_id, students[0], review_due=None)
    assert plan.status(TODAY) == "no_review_date"
    assert plan.is_current(TODAY) is True


# ── the list a supervisor reads ──────────────────────────────────────────────
@pytest.mark.django_db
def test_expired_plans_are_shown_not_hidden(nurse, tenant_id, students):
    """
    A lapsed anaphylaxis plan is the most important thing on the page. Filtering
    it out because the paperwork is overdue is the worst reading of "current".
    """
    _plan(tenant_id, students[0], review_due=TODAY - timedelta(days=30))
    resp = nurse.get("/api/v1/health/action-plans/critical/")

    assert resp.data["count"] == 1
    assert resp.data["results"][0]["status"] == "expired"


@pytest.mark.django_db
def test_critical_plans_and_expired_ones_sort_first(nurse, tenant_id, students):
    _plan(tenant_id, students[0], severity="moderate", plan_type="asthma",
          emergency_steps="Reliever, 4 puffs.")
    _plan(tenant_id, students[1], severity="critical",
          review_due=TODAY - timedelta(days=5))
    _plan(tenant_id, students[2], severity="critical", plan_type="diabetes",
          emergency_steps="Check BGL.")

    rows = nurse.get("/api/v1/health/action-plans/critical/").data["results"]
    # Critical before moderate; within critical, expired before current.
    assert rows[0]["severity"] == "critical" and rows[0]["status"] == "expired"
    assert rows[-1]["severity"] == "moderate"


@pytest.mark.django_db
def test_the_review_chase_list_excludes_current_plans(nurse, tenant_id, students):
    _plan(tenant_id, students[0])                                        # current
    _plan(tenant_id, students[1], review_due=TODAY - timedelta(days=5))  # expired
    _plan(tenant_id, students[2], review_due=None)                       # no date

    rows = nurse.get("/api/v1/health/action-plans/needing-review/").data["results"]
    assert {r["status"] for r in rows} == {"expired", "no_review_date"}


@pytest.mark.django_db
def test_plans_can_be_pulled_for_an_excursion_party(nurse, tenant_id, students):
    """What a teacher takes with them when they leave the site."""
    section = ClassSection.objects.create(tenant_id=tenant_id, name="8A", year_level=8)
    for s in students[:2]:
        Enrolment.objects.create(
            tenant_id=tenant_id, student=s, class_section=section, status="active"
        )
    _plan(tenant_id, students[0])
    _plan(tenant_id, students[2])  # not on the excursion

    resp = nurse.get(f"/api/v1/health/action-plans/for-group/?class_section={section.id}")
    assert resp.data["count"] == 1
    assert resp.data["results"][0]["student"] == str(students[0].id)


@pytest.mark.django_db
def test_for_group_without_a_cohort_is_refused(nurse):
    assert nurse.get("/api/v1/health/action-plans/for-group/").status_code == 400


# ── what a plan must contain ─────────────────────────────────────────────────
@pytest.mark.django_db
def test_a_plan_without_steps_is_refused(nurse, students):
    """A plan with no steps is not a plan."""
    resp = nurse.post("/api/v1/health/action-plans/", {
        "student": str(students[0].id), "plan_type": "asthma",
        "emergency_steps": "   ",
    }, format="json")
    # DRF's own blank check fires before the serializer's `validate`, so the
    # wording varies. What matters is that it is refused and names the field.
    assert resp.status_code == 400
    assert "emergency_steps" in str(resp.data)


@pytest.mark.django_db
def test_medication_without_a_location_is_refused(nurse, students):
    """
    Knowing a child needs an EpiPen without knowing where it is does not help.
    """
    resp = nurse.post("/api/v1/health/action-plans/", {
        "student": str(students[0].id), "plan_type": "anaphylaxis",
        "emergency_steps": "EpiPen to outer thigh.",
        "medication": "EpiPen Jr 150mcg",
    }, format="json")
    assert resp.status_code == 400
    assert "where the medication is kept" in str(resp.data)


@pytest.mark.django_db
def test_one_plan_per_student_per_type(nurse, tenant_id, students):
    """Two anaphylaxis plans for one child means one of them is wrong."""
    from django.db import IntegrityError

    _plan(tenant_id, students[0])
    with pytest.raises(IntegrityError):
        _plan(tenant_id, students[0])


# ── access ───────────────────────────────────────────────────────────────────
@pytest.mark.django_db
def test_any_staff_member_can_read_a_plan(client_for, tenant_id, students):
    """
    Deliberately wider than the rest of health data: a plan a relief teacher
    cannot open is a plan that fails when it is needed. Reads are audited.
    """
    _plan(tenant_id, students[0])
    teacher = client_for(["teacher"], "relief@cyed.edu.au")
    resp = teacher.get("/api/v1/health/action-plans/critical/")
    assert resp.status_code == 200
    assert resp.data["count"] == 1


@pytest.mark.django_db
def test_families_cannot_read_the_whole_schools_plans(client_for, tenant_id, students):
    _plan(tenant_id, students[0])
    parent = client_for(["parent"], "p@example.com")
    assert parent.get("/api/v1/health/action-plans/critical/").status_code == 403
