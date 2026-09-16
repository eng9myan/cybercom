"""
Individual education plans.

These replace a boolean flag. The tests are mostly about the properties that
make a plan *evidence* rather than a document: it changes something, the family
was consulted, it was reviewed with named people, and the NCCD return is
derived from it rather than typed in beside it.
"""

import uuid
from datetime import date, timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from products.cyed.wellbeing import support_plans
from products.cyed.wellbeing.models import (
    LearnerProfile,
    SupportAdjustment,
    SupportGoal,
    SupportPlan,
)
from products.cyed.sis.models import Student

TODAY = timezone.localdate()


@pytest.fixture
def client_for(mint_token, mock_jwks, tenant_id):
    def _make(roles, email="coordinator@cyed.edu.au"):
        c = APIClient()
        c.credentials(HTTP_AUTHORIZATION=f"Bearer {mint_token({
            'sub': str(uuid.uuid4()), 'email': email, 'tenant_id': str(tenant_id),
            'realm_access': {'roles': roles},
        })}")
        return c
    return _make


@pytest.fixture
def coordinator(client_for):
    return client_for(["pastoral"])


@pytest.fixture
def student(tenant_id):
    s = Student.objects.create(
        tenant_id=tenant_id, first_name="Mia", last_name="Tran", year_level=8,
        enrolment_status="enrolled",
    )
    LearnerProfile.objects.create(tenant_id=tenant_id, student=s)
    return s


def _plan(tenant_id, student, **extra):
    body = {
        "tenant_id": tenant_id,
        "student": student,
        "plan_type": "iep",
        "needs": "Difficulty sustaining attention in extended written tasks.",
        "family_consulted_on": TODAY - timedelta(days=10),
        "review_due": TODAY + timedelta(days=180),
    }
    body.update(extra)
    return SupportPlan.objects.create(**body)


def _adjustment(tenant_id, plan, **extra):
    body = {
        "tenant_id": tenant_id,
        "plan": plan,
        "category": "assessment",
        "description": "Extra time of 25% on all written assessments, in a quiet room.",
        "nccd_level": "supplementary",
        "responsible": "Classroom teacher",
    }
    body.update(extra)
    return SupportAdjustment.objects.create(**body)


# ── a plan has to change something ───────────────────────────────────────────
@pytest.mark.django_db
def test_a_plan_with_no_adjustments_cannot_be_activated(coordinator, tenant_id, student):
    """
    A plan that changes nothing is not evidence of support, and reporting it to
    NCCD would be a claim the school cannot stand behind.
    """
    plan = _plan(tenant_id, student)
    resp = coordinator.post(f"/api/v1/wellbeing/support-plans/{plan.id}/activate/", {},
                            format="json")
    assert resp.status_code == 409
    assert "not evidence of support" in resp.data["detail"]


@pytest.mark.django_db
def test_activating_a_plan_with_adjustments_works(coordinator, tenant_id, student):
    plan = _plan(tenant_id, student)
    _adjustment(tenant_id, plan)

    resp = coordinator.post(f"/api/v1/wellbeing/support-plans/{plan.id}/activate/", {},
                            format="json")
    assert resp.status_code == 200, resp.data
    assert resp.data["status"] == "active"
    assert resp.data["nccd_level"] == "supplementary"


@pytest.mark.django_db
def test_a_vague_adjustment_is_refused(coordinator, tenant_id, student):
    """"Provide support as needed" is what a relief teacher cannot act on."""
    plan = _plan(tenant_id, student)
    resp = coordinator.post("/api/v1/wellbeing/support-adjustments/", {
        "plan": str(plan.id), "category": "instruction", "description": "Help him",
    }, format="json")
    assert resp.status_code == 400
    assert "concrete enough" in str(resp.data)


# ── history survives ─────────────────────────────────────────────────────────
@pytest.mark.django_db
def test_activating_a_new_plan_supersedes_the_old_one(coordinator, tenant_id, student):
    """
    "What was in force last March" is the question asked when something has
    gone wrong; a plan edited in place cannot answer it.
    """
    first = _plan(tenant_id, student)
    _adjustment(tenant_id, first)
    support_plans.activate(first)

    second = _plan(tenant_id, student)
    _adjustment(tenant_id, second, nccd_level="substantial")
    support_plans.activate(second)

    first.refresh_from_db()
    assert first.status == "superseded"
    assert first.superseded_by_id == second.id
    assert SupportPlan.objects.filter(student=student, status="active").count() == 1


@pytest.mark.django_db
def test_a_superseded_plan_cannot_be_reactivated(tenant_id, student):
    first = _plan(tenant_id, student)
    _adjustment(tenant_id, first)
    support_plans.activate(first)
    second = _plan(tenant_id, student)
    _adjustment(tenant_id, second)
    support_plans.activate(second)

    with pytest.raises(support_plans.SupportPlanError):
        support_plans.activate(first)


@pytest.mark.django_db
def test_a_different_plan_type_does_not_supersede(tenant_id, student):
    """A behaviour plan and an IEP coexist; they are about different things."""
    iep = _plan(tenant_id, student, plan_type="iep")
    _adjustment(tenant_id, iep)
    support_plans.activate(iep)

    behaviour = _plan(tenant_id, student, plan_type="behaviour")
    _adjustment(tenant_id, behaviour, category="safety")
    support_plans.activate(behaviour)

    iep.refresh_from_db()
    assert iep.status == "active"


# ── the flag becomes derived ─────────────────────────────────────────────────
@pytest.mark.django_db
def test_the_learner_profile_flag_follows_the_plan(tenant_id, student):
    """
    The boolean stays for the code that reads it, but it is now a cached answer
    rather than the only record that a plan exists.
    """
    profile = LearnerProfile.objects.get(student=student)
    assert profile.has_individual_plan is False

    plan = _plan(tenant_id, student)
    _adjustment(tenant_id, plan)
    support_plans.activate(plan)
    profile.refresh_from_db()
    assert profile.has_individual_plan is True

    support_plans.close(plan, reason="Student no longer requires adjustments")
    profile.refresh_from_db()
    assert profile.has_individual_plan is False


@pytest.mark.django_db
def test_closing_needs_a_reason(tenant_id, student):
    plan = _plan(tenant_id, student)
    _adjustment(tenant_id, plan)
    support_plans.activate(plan)
    with pytest.raises(support_plans.SupportPlanError):
        support_plans.close(plan, reason="  ")


# ── reviews ──────────────────────────────────────────────────────────────────
@pytest.mark.django_db
def test_a_review_records_who_was_there_and_rolls_the_date(coordinator, tenant_id, student):
    plan = _plan(tenant_id, student)
    _adjustment(tenant_id, plan)
    support_plans.activate(plan)

    next_due = (TODAY + timedelta(days=180)).isoformat()
    resp = coordinator.post(f"/api/v1/wellbeing/support-plans/{plan.id}/record-review/", {
        "held_on": TODAY.isoformat(),
        "participants": "H Tran (mother), A Lovelace (teacher), J Singh (coordinator)",
        "family_present": True,
        "outcome": "Extra time continues; add scribe for extended responses.",
        "next_review_due": next_due,
    }, format="json")

    assert resp.status_code == 201, resp.data
    assert resp.data["family_present"] is True
    plan.refresh_from_db()
    assert plan.review_due.isoformat() == next_due


@pytest.mark.django_db
def test_a_review_with_nobody_present_is_refused(coordinator, tenant_id, student):
    """A review with no participants is not evidence that one happened."""
    plan = _plan(tenant_id, student)
    resp = coordinator.post(f"/api/v1/wellbeing/support-plans/{plan.id}/record-review/", {
        "held_on": TODAY.isoformat(), "participants": "   ",
    }, format="json")
    assert resp.status_code == 400


@pytest.mark.django_db
def test_overdue_plans_head_the_coordinators_worklist(coordinator, tenant_id):
    for name, due in [("Overdue", TODAY - timedelta(days=30)),
                      ("Soon", TODAY + timedelta(days=10)),
                      ("Fine", TODAY + timedelta(days=300))]:
        s = Student.objects.create(
            tenant_id=tenant_id, first_name=name, last_name="Student",
            year_level=8, enrolment_status="enrolled",
        )
        plan = _plan(tenant_id, s, review_due=due)
        _adjustment(tenant_id, plan)
        support_plans.activate(plan)

    resp = coordinator.get("/api/v1/wellbeing/support-plans/needing-review/")
    names = [r["name"] for r in resp.data["results"]]
    assert names[0].startswith("Overdue")
    assert "Fine Student" not in names


# ── NCCD evidence ────────────────────────────────────────────────────────────
@pytest.mark.django_db
def test_the_nccd_return_is_derived_from_the_adjustments(coordinator, tenant_id, student):
    """
    A return typed in separately drifts from the plan. This one cannot: the
    level reported *is* the highest adjustment recorded.
    """
    plan = _plan(tenant_id, student)
    _adjustment(tenant_id, plan, nccd_level="supplementary")
    _adjustment(tenant_id, plan, category="curriculum", nccd_level="extensive",
                description="Modified curriculum in mathematics, working at Year 5 level.")
    support_plans.activate(plan)
    support_plans.record_review(
        plan, held_on=TODAY, participants="Family and coordinator", family_present=True
    )

    resp = coordinator.get("/api/v1/wellbeing/support-plans/nccd-evidence/")
    row = resp.data["results"][0]
    assert row["adjustment_level"] == "extensive"
    assert row["adjustment_count"] == 2
    assert set(row["categories"]) == {"assessment", "curriculum"}
    assert row["evidence_complete"] is True


@pytest.mark.django_db
def test_thin_evidence_is_flagged_not_hidden(coordinator, tenant_id, student):
    """
    A school needs to see which of its claims would not survive an audit before
    an auditor does.
    """
    plan = _plan(tenant_id, student, family_consulted_on=None)
    _adjustment(tenant_id, plan)
    support_plans.activate(plan)

    resp = coordinator.get("/api/v1/wellbeing/support-plans/nccd-evidence/")
    assert resp.data["incomplete_evidence"] == 1
    assert resp.data["results"][0]["evidence_complete"] is False


@pytest.mark.django_db
def test_draft_plans_are_not_reported(coordinator, tenant_id, student):
    plan = _plan(tenant_id, student)
    _adjustment(tenant_id, plan)
    resp = coordinator.get("/api/v1/wellbeing/support-plans/nccd-evidence/")
    assert resp.data["count"] == 0


# ── access ───────────────────────────────────────────────────────────────────
@pytest.mark.django_db
def test_a_teacher_can_read_the_adjustments_they_must_follow(
    client_for, tenant_id, student
):
    """A plan a relief teacher cannot open is one that does not get followed."""
    plan = _plan(tenant_id, student)
    _adjustment(tenant_id, plan)
    support_plans.activate(plan)

    teacher = client_for(["teacher"], "relief@cyed.edu.au")
    resp = teacher.get(f"/api/v1/wellbeing/support-adjustments/for-student/?student={student.id}")
    assert resp.status_code == 200
    assert resp.data["count"] == 1


@pytest.mark.django_db
def test_a_teacher_cannot_read_the_whole_plan(client_for, tenant_id, student):
    """The diagnosis, family notes and the student's own words stay pastoral."""
    plan = _plan(tenant_id, student)
    teacher = client_for(["teacher"], "relief@cyed.edu.au")
    assert teacher.get(f"/api/v1/wellbeing/support-plans/{plan.id}/").status_code == 403


@pytest.mark.django_db
def test_superseded_adjustments_are_not_served_to_teachers(
    client_for, tenant_id, student
):
    """Following a withdrawn adjustment would be actively wrong."""
    first = _plan(tenant_id, student)
    _adjustment(tenant_id, first, description="Old approach that has since been replaced.")
    support_plans.activate(first)

    second = _plan(tenant_id, student)
    _adjustment(tenant_id, second, description="Current approach, replacing the earlier one.")
    support_plans.activate(second)

    teacher = client_for(["teacher"], "relief@cyed.edu.au")
    resp = teacher.get(f"/api/v1/wellbeing/support-adjustments/for-student/?student={student.id}")
    assert resp.data["count"] == 1
    assert "Current approach" in resp.data["results"][0]["description"]


@pytest.mark.django_db
def test_families_cannot_read_support_plans(client_for, tenant_id, student):
    plan = _plan(tenant_id, student)
    parent = client_for(["parent"], "p@example.com")
    assert parent.get(f"/api/v1/wellbeing/support-plans/{plan.id}/").status_code == 403


# ── goals ────────────────────────────────────────────────────────────────────
@pytest.mark.django_db
def test_goal_progress_is_recorded_with_a_date(coordinator, tenant_id, student):
    """An adjustment nobody can say worked is not evidence of anything."""
    plan = _plan(tenant_id, student)
    goal = SupportGoal.objects.create(
        tenant_id=tenant_id, plan=plan,
        description="Complete a 300-word written response within a single lesson.",
        success_criteria="Three consecutive tasks completed in class time.",
    )
    resp = coordinator.post(f"/api/v1/wellbeing/support-goals/{goal.id}/record-progress/", {
        "progress": "working_towards", "note": "Two of three achieved this term.",
    }, format="json")

    assert resp.status_code == 200
    goal.refresh_from_db()
    assert goal.progress == "working_towards"
    assert goal.progress_updated_on == TODAY
