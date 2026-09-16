"""
Parent absence explanations.

The rule that shapes everything here: an explanation is a *claim*, not a
correction. Attendance is a legal record the department audits, so submitting
an explanation must never change it — only a staff acceptance does.
"""

import uuid
from datetime import date, timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from products.cyed.attendance.models import AbsenceExplanation, AttendanceMark, RollCall
from products.cyed.notifications.models import Notification
from products.cyed.sis.models import ClassSection, Enrolment, Guardian, Student

TODAY = timezone.localdate()


@pytest.fixture
def client_for(mint_token, mock_jwks, tenant_id):
    def _make(roles, email):
        c = APIClient()
        c.credentials(HTTP_AUTHORIZATION=f"Bearer {mint_token({
            'sub': str(uuid.uuid4()), 'email': email, 'tenant_id': str(tenant_id),
            'realm_access': {'roles': roles},
        })}")
        return c
    return _make


@pytest.fixture
def office(client_for):
    return client_for(["tenant_admin"], "office@cyed.edu.au")


@pytest.fixture
def parent(client_for):
    return client_for(["parent"], "hoa@example.com")


@pytest.fixture
def school(tenant_id):
    section = ClassSection.objects.create(tenant_id=tenant_id, name="8A", year_level=8)
    mia = Student.objects.create(
        tenant_id=tenant_id, first_name="Mia", last_name="Tran", year_level=8,
        enrolment_status="enrolled",
    )
    Enrolment.objects.create(
        tenant_id=tenant_id, student=mia, class_section=section, status="active"
    )
    guardian = Guardian.objects.create(
        tenant_id=tenant_id, first_name="Hoa", last_name="Tran", email="hoa@example.com"
    )
    guardian.students.add(mia)

    other = Student.objects.create(
        tenant_id=tenant_id, first_name="Ken", last_name="Ito", year_level=8,
        enrolment_status="enrolled",
    )
    Enrolment.objects.create(
        tenant_id=tenant_id, student=other, class_section=section, status="active"
    )
    return section, mia, other


def _mark_absent(tenant_id, section, student, day, status="absent"):
    roll = RollCall.objects.create(
        tenant_id=tenant_id, class_section=section, date=day, period_label="P1"
    )
    return AttendanceMark.objects.create(
        tenant_id=tenant_id, roll_call=roll, student=student, status=status
    )


def _submit(client, student, **extra):
    body = {
        "student": str(student.id),
        "kind": "absence",
        "start_date": TODAY.isoformat(),
        "end_date": TODAY.isoformat(),
        "reason": "illness",
        "detail": "Home with a temperature.",
    }
    body.update(extra)
    return client.post("/api/v1/attendance/explanations/", body, format="json")


# ── submitting ───────────────────────────────────────────────────────────────
@pytest.mark.django_db
def test_a_parent_can_explain_their_childs_absence(parent, school):
    _section, mia, _other = school
    resp = _submit(parent, mia)
    assert resp.status_code == 201, resp.data
    assert resp.data["status"] == "submitted"
    assert resp.data["submitted_by_email"] == "hoa@example.com"


@pytest.mark.django_db
def test_submitting_does_not_change_the_attendance_record(parent, tenant_id, school):
    """
    The core rule. Attendance is audited; letting a family rewrite it directly
    would make it worthless as evidence.
    """
    section, mia, _other = school
    mark = _mark_absent(tenant_id, section, mia, TODAY)

    _submit(parent, mia)

    mark.refresh_from_db()
    assert mark.status == "absent"


@pytest.mark.django_db
def test_a_parent_cannot_explain_another_familys_child(parent, school):
    _section, _mia, other = school
    resp = _submit(parent, other)
    assert resp.status_code == 403
    assert "your own child" in str(resp.data)


@pytest.mark.django_db
def test_a_parent_sees_only_their_own_submissions(parent, office, tenant_id, school):
    _section, mia, other = school
    _submit(parent, mia)
    office.post("/api/v1/attendance/explanations/", {
        "student": str(other.id), "start_date": TODAY.isoformat(),
        "end_date": TODAY.isoformat(), "reason": "family",
    }, format="json")

    resp = parent.get("/api/v1/attendance/explanations/")
    rows = resp.data["results"] if isinstance(resp.data, dict) else resp.data
    assert len(rows) == 1
    assert str(rows[0]["student"]) == str(mia.id)


@pytest.mark.django_db
def test_an_end_date_before_the_start_is_refused(parent, school):
    _section, mia, _other = school
    resp = _submit(parent, mia, end_date=(TODAY - timedelta(days=2)).isoformat())
    assert resp.status_code == 400


@pytest.mark.django_db
def test_an_unbounded_range_is_refused(parent, school):
    """One submission must not be able to excuse a year of marks."""
    _section, mia, _other = school
    resp = _submit(parent, mia, end_date=(TODAY + timedelta(days=200)).isoformat())
    assert resp.status_code == 400
    assert "at most 31 days" in str(resp.data)


# ── review ───────────────────────────────────────────────────────────────────
@pytest.mark.django_db
def test_accepting_excuses_the_marks_it_covers(office, parent, tenant_id, school):
    section, mia, _other = school
    mark = _mark_absent(tenant_id, section, mia, TODAY)
    explanation = _submit(parent, mia).data["id"]

    resp = office.post(f"/api/v1/attendance/explanations/{explanation}/accept/", {}, format="json")
    assert resp.status_code == 200, resp.data
    assert resp.data["marks_excused"] == 1

    mark.refresh_from_db()
    assert mark.status == "excused"
    assert "Illness" in mark.note


@pytest.mark.django_db
def test_accepting_a_multi_day_explanation_excuses_every_day(
    office, parent, tenant_id, school
):
    section, mia, _other = school
    for offset in range(3):
        _mark_absent(tenant_id, section, mia, TODAY - timedelta(days=offset))

    explanation = _submit(
        parent, mia,
        start_date=(TODAY - timedelta(days=2)).isoformat(),
        end_date=TODAY.isoformat(),
    ).data["id"]
    resp = office.post(f"/api/v1/attendance/explanations/{explanation}/accept/", {}, format="json")
    assert resp.data["marks_excused"] == 3


@pytest.mark.django_db
def test_a_present_day_inside_the_range_is_left_alone(office, parent, tenant_id, school):
    """
    Rewriting a day the student attended would corrupt the record the
    department audits.
    """
    section, mia, _other = school
    present = _mark_absent(tenant_id, section, mia, TODAY - timedelta(days=1), status="present")
    _mark_absent(tenant_id, section, mia, TODAY)

    explanation = _submit(
        parent, mia,
        start_date=(TODAY - timedelta(days=1)).isoformat(),
        end_date=TODAY.isoformat(),
    ).data["id"]
    resp = office.post(f"/api/v1/attendance/explanations/{explanation}/accept/", {}, format="json")

    assert resp.data["marks_excused"] == 1
    present.refresh_from_db()
    assert present.status == "present"


@pytest.mark.django_db
def test_declining_requires_a_reason(office, parent, school):
    _section, mia, _other = school
    explanation = _submit(parent, mia).data["id"]

    bare = office.post(f"/api/v1/attendance/explanations/{explanation}/decline/", {}, format="json")
    assert bare.status_code == 400

    resp = office.post(f"/api/v1/attendance/explanations/{explanation}/decline/", {
        "note": "Please provide a medical certificate for absences over three days.",
    }, format="json")
    assert resp.status_code == 200
    assert resp.data["status"] == "declined"


@pytest.mark.django_db
def test_a_parent_cannot_review_their_own_explanation(parent, school):
    _section, mia, _other = school
    explanation = _submit(parent, mia).data["id"]
    resp = parent.post(f"/api/v1/attendance/explanations/{explanation}/accept/", {}, format="json")
    assert resp.status_code == 403


@pytest.mark.django_db
def test_reviewing_twice_is_refused(office, parent, school):
    _section, mia, _other = school
    explanation = _submit(parent, mia).data["id"]
    office.post(f"/api/v1/attendance/explanations/{explanation}/accept/", {}, format="json")
    again = office.post(f"/api/v1/attendance/explanations/{explanation}/accept/", {}, format="json")
    assert again.status_code == 409


@pytest.mark.django_db
def test_a_reviewed_explanation_can_no_longer_be_edited(office, parent, school):
    _section, mia, _other = school
    explanation = _submit(parent, mia).data["id"]
    office.post(f"/api/v1/attendance/explanations/{explanation}/accept/", {}, format="json")

    resp = parent.patch(
        f"/api/v1/attendance/explanations/{explanation}/",
        {"detail": "Actually a dentist appointment"}, format="json",
    )
    assert resp.status_code == 409


@pytest.mark.django_db
def test_the_review_queue_is_staff_only(parent, office, school):
    _section, mia, _other = school
    _submit(parent, mia)
    assert parent.get("/api/v1/attendance/explanations/pending/").status_code == 403
    assert office.get("/api/v1/attendance/explanations/pending/").data["count"] == 1


# ── explaining ahead of time ─────────────────────────────────────────────────
@pytest.mark.django_db(transaction=True)
def test_an_absence_explained_in_advance_does_not_alert_the_parent(
    office, parent, tenant_id, school
):
    """
    Telling the school on Monday about Tuesday must prevent Tuesday's alert.
    Otherwise families learn that telling the school achieves nothing.
    """
    section, mia, _other = school
    tomorrow = TODAY + timedelta(days=1)

    explanation = _submit(
        parent, mia, start_date=tomorrow.isoformat(), end_date=tomorrow.isoformat(),
        reason="medical",
    ).data["id"]
    accepted = office.post(
        f"/api/v1/attendance/explanations/{explanation}/accept/", {}, format="json"
    )
    # Nothing to excuse yet — the absence has not happened.
    assert accepted.data["marks_excused"] == 0
    assert accepted.data["planned"] is True

    taken = office.post("/api/v1/attendance/roll-calls/take/", {
        "class_section": str(section.id),
        "date": tomorrow.isoformat(),
        "marks": [{"student": str(mia.id), "status": "absent"}],
    }, format="json")
    assert taken.status_code == 200, taken.data
    assert taken.data["pre_explained"] == 1
    assert taken.data["notified"] == 0

    mark = AttendanceMark.objects.get(student=mia, roll_call__date=tomorrow)
    assert mark.status == "excused"
    assert Notification.objects.filter(tenant_id=tenant_id, category="attendance").count() == 0


@pytest.mark.django_db(transaction=True)
def test_an_unexplained_absence_still_alerts(office, tenant_id, school):
    """The pre-explained path must not suppress alerts for everyone else."""
    section, _mia, other = school
    guardian = Guardian.objects.create(
        tenant_id=tenant_id, first_name="Yui", last_name="Ito", email="yui@example.com"
    )
    guardian.students.add(other)

    taken = office.post("/api/v1/attendance/roll-calls/take/", {
        "class_section": str(section.id),
        "date": TODAY.isoformat(),
        "marks": [{"student": str(other.id), "status": "absent"}],
    }, format="json")
    assert taken.data["notified"] == 1
