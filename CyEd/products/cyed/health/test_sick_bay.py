"""
Sick bay visits.

The point of this feature is that telling a parent stops being something a
person has to remember. Most of these tests are about that: the alert is a
consequence of the outcome, it goes out through the real delivery path, and a
child released to nobody in particular is refused.
"""

import uuid

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from products.cyed.health.models import ActionPlan, SickBayVisit
from products.cyed.notifications.models import Notification
from products.cyed.sis.models import ClassSection, Enrolment, Guardian, Student

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
def student(tenant_id):
    s = Student.objects.create(
        tenant_id=tenant_id, first_name="Mia", last_name="Tran", year_level=8,
        enrolment_status="enrolled",
    )
    guardian = Guardian.objects.create(
        tenant_id=tenant_id, first_name="Hoa", last_name="Tran",
        email="hoa@example.com", phone="+61400111222",
    )
    guardian.students.add(s)
    return s


def _open(client, student, **extra):
    body = {"student": str(student.id), "complaint": "Headache and feels hot."}
    body.update(extra)
    return client.post("/api/v1/health/sick-bay/", body, format="json")


# ── who is here now ──────────────────────────────────────────────────────────
@pytest.mark.django_db
def test_a_visit_opens_and_shows_in_current(nurse, student):
    resp = _open(nurse, student)
    assert resp.status_code == 201, resp.data
    assert resp.data["is_open"] is True

    current = nurse.get("/api/v1/health/sick-bay/current/")
    assert current.data["count"] == 1
    assert current.data["results"][0]["name"] == "Mia Tran"


@pytest.mark.django_db
def test_the_referring_adult_defaults_to_whoever_logged_it(nurse, student):
    resp = _open(nurse, student)
    assert resp.data["referred_by"] == "nurse@cyed.edu.au"


@pytest.mark.django_db
def test_a_student_with_an_action_plan_is_flagged(nurse, tenant_id, student):
    """
    A child with a known condition presenting unwell is a different situation
    from one who tripped over.
    """
    ActionPlan.objects.create(
        tenant_id=tenant_id, student=student, plan_type="asthma",
        emergency_steps="Reliever, 4 puffs.",
    )
    _open(nurse, student)
    current = nurse.get("/api/v1/health/sick-bay/current/")
    assert current.data["results"][0]["has_action_plan"] is True


@pytest.mark.django_db
def test_a_closed_visit_leaves_the_current_list(nurse, student):
    visit = _open(nurse, student).data["id"]
    nurse.post(f"/api/v1/health/sick-bay/{visit}/close/", {
        "outcome": "returned_to_class",
    }, format="json")
    assert nurse.get("/api/v1/health/sick-bay/current/").data["count"] == 0


# ── the alert ────────────────────────────────────────────────────────────────
@pytest.mark.django_db
def test_sending_a_child_home_messages_the_guardians(nurse, tenant_id, student):
    """
    The whole point: the alert is a consequence of the outcome, not a checkbox
    somebody has to remember to tick.
    """
    visit = _open(nurse, student).data["id"]
    resp = nurse.post(f"/api/v1/health/sick-bay/{visit}/close/", {
        "outcome": "sent_home", "collected_by": "Hoa Tran (mother)",
    }, format="json")

    assert resp.status_code == 200, resp.data
    assert resp.data["guardians_notified"] == 1

    note = Notification.objects.get(tenant_id=tenant_id, category="wellbeing")
    assert note.recipient_phone == "+61400111222"
    assert note.channel == "sms"
    assert "needs collecting" in note.subject


@pytest.mark.django_db
def test_an_emergency_says_so_plainly(nurse, tenant_id, student):
    visit = _open(nurse, student).data["id"]
    nurse.post(f"/api/v1/health/sick-bay/{visit}/close/", {
        "outcome": "emergency", "collected_by": "Ambulance",
    }, format="json")

    note = Notification.objects.get(tenant_id=tenant_id, category="wellbeing")
    assert "Urgent" in note.subject
    assert "emergency services" in note.body


@pytest.mark.django_db
def test_returning_to_class_does_not_message_anyone(nurse, tenant_id, student):
    """A child with a headache who felt better does not need a parent alarmed."""
    visit = _open(nurse, student).data["id"]
    nurse.post(f"/api/v1/health/sick-bay/{visit}/close/", {
        "outcome": "returned_to_class",
    }, format="json")
    assert Notification.objects.filter(tenant_id=tenant_id, category="wellbeing").count() == 0


@pytest.mark.django_db
def test_guardians_can_be_warned_before_the_visit_closes(nurse, tenant_id, student):
    """A family that might need to collect can start moving now."""
    visit = _open(nurse, student).data["id"]
    resp = nurse.post(f"/api/v1/health/sick-bay/{visit}/notify-guardians/", {}, format="json")

    assert resp.data["notified"] == 1
    assert SickBayVisit.objects.get(id=visit).is_open() is True


@pytest.mark.django_db
def test_a_guardian_without_a_phone_still_gets_told(nurse, tenant_id):
    """In-app rather than nothing — a missing number must not mean silence."""
    s = Student.objects.create(
        tenant_id=tenant_id, first_name="Ken", last_name="Ito", year_level=8,
        enrolment_status="enrolled",
    )
    Guardian.objects.create(
        tenant_id=tenant_id, first_name="Yui", last_name="Ito", email="yui@example.com"
    ).students.add(s)

    visit = _open(nurse, s).data["id"]
    nurse.post(f"/api/v1/health/sick-bay/{visit}/close/", {
        "outcome": "sent_home", "collected_by": "Yui Ito",
    }, format="json")

    note = Notification.objects.get(tenant_id=tenant_id, category="wellbeing")
    assert note.channel == "in_app"


# ── refusals ─────────────────────────────────────────────────────────────────
@pytest.mark.django_db
def test_sending_a_child_home_needs_a_named_collector(nurse, student):
    """A child released to nobody in particular is a safeguarding failure."""
    visit = _open(nurse, student).data["id"]
    resp = nurse.post(f"/api/v1/health/sick-bay/{visit}/close/", {
        "outcome": "sent_home",
    }, format="json")
    assert resp.status_code == 409
    assert "who collected" in resp.data["detail"]


@pytest.mark.django_db
def test_closing_twice_is_refused(nurse, student):
    visit = _open(nurse, student).data["id"]
    nurse.post(f"/api/v1/health/sick-bay/{visit}/close/",
               {"outcome": "returned_to_class"}, format="json")
    again = nurse.post(f"/api/v1/health/sick-bay/{visit}/close/",
                       {"outcome": "returned_to_class"}, format="json")
    assert again.status_code == 409


@pytest.mark.django_db
def test_in_progress_is_not_a_closing_outcome(nurse, student):
    visit = _open(nurse, student).data["id"]
    resp = nurse.post(f"/api/v1/health/sick-bay/{visit}/close/",
                      {"outcome": "in_progress"}, format="json")
    assert resp.status_code == 409


@pytest.mark.django_db
def test_the_outcome_cannot_be_patched_around_the_alert(nurse, student):
    """PATCHing `outcome` would let a visit be 'sent home' with nobody told."""
    visit = _open(nurse, student).data["id"]
    nurse.patch(f"/api/v1/health/sick-bay/{visit}/",
                {"outcome": "sent_home"}, format="json")
    assert SickBayVisit.objects.get(id=visit).outcome == "in_progress"


@pytest.mark.django_db
def test_families_cannot_read_the_sick_bay_log(client_for, student):
    parent = client_for(["parent"], "hoa@example.com")
    assert parent.get("/api/v1/health/sick-bay/current/").status_code == 403


# ── the day's log, and the emergency roll ────────────────────────────────────
@pytest.mark.django_db
def test_the_day_log_counts_outcomes(nurse, tenant_id, student):
    for outcome in ("returned_to_class", "sent_home"):
        visit = _open(nurse, student).data["id"]
        nurse.post(f"/api/v1/health/sick-bay/{visit}/close/", {
            "outcome": outcome, "collected_by": "Hoa Tran",
        }, format="json")

    day = nurse.get("/api/v1/health/sick-bay/day/")
    assert day.data["count"] == 2
    assert day.data["by_outcome"] == {"returned_to_class": 1, "sent_home": 1}


@pytest.mark.django_db
def test_a_student_in_the_sick_bay_shows_there_on_the_emergency_roll(
    client_for, nurse, tenant_id, student
):
    """
    Otherwise the class teacher reports them missing and someone goes back
    inside for a child who is already accounted for.
    """
    office = client_for(["tenant_admin"], "office@cyed.edu.au")
    section = ClassSection.objects.create(tenant_id=tenant_id, name="8A", year_level=8)
    Enrolment.objects.create(
        tenant_id=tenant_id, student=student, class_section=section, status="active"
    )
    office.post("/api/v1/attendance/roll-calls/take/", {
        "class_section": str(section.id), "date": TODAY.isoformat(),
    }, format="json")

    _open(nurse, student)

    roll = office.get("/api/v1/attendance/emergency-drills/on-site/")
    sick_bay = [s for s in roll.data["sections"] if s["class_section"] == "Sick bay"]
    assert len(sick_bay) == 1
    assert sick_bay[0]["students"][0]["name"] == "Mia Tran"
