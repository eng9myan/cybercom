"""
Bulk roll marking.

Covers the two problems the audit named: thirty requests to mark thirty
students, and guardian notifications sent from inside the write transaction.
"""

import uuid

import pytest
from django.db import transaction
from rest_framework.test import APIClient

from products.cyed.attendance.models import AttendanceMark, RollCall
from products.cyed.notifications.models import Notification
from products.cyed.sis.models import ClassSection, Enrolment, Guardian, Student


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
    """A class of five, each with a guardian."""
    section = ClassSection.objects.create(tenant_id=tenant_id, name="8A Mathematics", year_level=8)
    students = []
    for i, name in enumerate(["Ana", "Ben", "Cara", "Dev", "Eve"]):
        student = Student.objects.create(
            tenant_id=tenant_id, first_name=name, last_name=f"S{i}", year_level=8
        )
        guardian = Guardian.objects.create(
            tenant_id=tenant_id, first_name=f"P{i}", last_name=f"S{i}",
            email=f"p{i}@example.com",
        )
        student.guardians.add(guardian)
        Enrolment.objects.create(
            tenant_id=tenant_id, student=student, class_section=section, status="active"
        )
        students.append(student)
    return section, students


def _take(client, section, marks=None, **kwargs):
    body = {"class_section": str(section.id), "date": "2026-08-11", "period_label": "P1"}
    if marks is not None:
        body["marks"] = marks
    body.update(kwargs)
    return client.post("/api/v1/attendance/roll-calls/take/", body, format="json")


# ── the core promise ─────────────────────────────────────────────────────────
@pytest.mark.django_db
def test_one_request_marks_the_whole_class(teacher_client, tenant_id, klass):
    section, students = klass
    resp = _take(teacher_client, section, marks=[{"student": str(students[1].id), "status": "absent"}])

    assert resp.status_code == 200, resp.data
    assert resp.data["roster"] == 5
    assert resp.data["created"] == 5
    assert resp.data["by_status"] == {"present": 4, "absent": 1}
    assert AttendanceMark.objects.filter(tenant_id=tenant_id).count() == 5


@pytest.mark.django_db
def test_sending_no_marks_records_the_class_present(teacher_client, klass):
    section, _ = klass
    resp = _take(teacher_client, section)
    assert resp.data["by_status"] == {"present": 5}


@pytest.mark.django_db
def test_default_status_can_be_flipped_for_an_excursion(teacher_client, klass):
    """Whole class out; the exceptions are the ones who stayed behind."""
    section, students = klass
    resp = _take(
        teacher_client, section,
        marks=[{"student": str(students[0].id), "status": "present"}],
        default_status="excused",
    )
    assert resp.data["by_status"] == {"excused": 4, "present": 1}


@pytest.mark.django_db
def test_resubmitting_corrects_rather_than_duplicates(teacher_client, tenant_id, klass):
    """A teacher fixing a mistake five minutes later is the normal case."""
    section, students = klass
    _take(teacher_client, section, marks=[{"student": str(students[1].id), "status": "absent"}])
    second = _take(teacher_client, section, marks=[{"student": str(students[1].id), "status": "late",
                                                   "minutes_late": 12}])

    assert second.data["created"] == 0
    assert second.data["updated"] == 1
    assert second.data["unchanged"] == 4
    assert AttendanceMark.objects.filter(tenant_id=tenant_id).count() == 5
    mark = AttendanceMark.objects.get(student=students[1])
    assert mark.status == "late" and mark.minutes_late == 12
    assert RollCall.objects.filter(tenant_id=tenant_id).count() == 1


# ── notifications ────────────────────────────────────────────────────────────
@pytest.mark.django_db(transaction=True)
def test_absences_notify_guardians_once_committed(teacher_client, tenant_id, klass):
    section, students = klass
    _take(teacher_client, section, marks=[
        {"student": str(students[1].id), "status": "absent"},
        {"student": str(students[2].id), "status": "late", "minutes_late": 5},
    ])
    notes = Notification.objects.filter(tenant_id=tenant_id, category="attendance")
    assert notes.count() == 2
    assert set(notes.values_list("recipient_email", flat=True)) == {"p1@example.com", "p2@example.com"}


@pytest.mark.django_db(transaction=True)
def test_present_students_do_not_notify_anyone(teacher_client, tenant_id, klass):
    section, _ = klass
    _take(teacher_client, section)
    assert Notification.objects.filter(tenant_id=tenant_id, category="attendance").count() == 0


@pytest.mark.django_db(transaction=True)
def test_correcting_an_absence_note_does_not_re_alert_the_parent(teacher_client, tenant_id, klass):
    """
    A parent must not get a second "your child is absent" message because the
    teacher fixed a typo in the note.
    """
    section, students = klass
    _take(teacher_client, section, marks=[{"student": str(students[1].id), "status": "absent"}])
    assert Notification.objects.filter(tenant_id=tenant_id, category="attendance").count() == 1

    _take(teacher_client, section, marks=[
        {"student": str(students[1].id), "status": "absent", "note": "Called home — flu"},
    ])
    assert Notification.objects.filter(tenant_id=tenant_id, category="attendance").count() == 1


@pytest.mark.django_db(transaction=True)
def test_marking_present_then_absent_does_alert(teacher_client, tenant_id, klass):
    """A real transition into absence must always reach the guardian."""
    section, students = klass
    _take(teacher_client, section)
    assert Notification.objects.filter(tenant_id=tenant_id, category="attendance").count() == 0

    _take(teacher_client, section, marks=[{"student": str(students[3].id), "status": "absent"}])
    notes = Notification.objects.filter(tenant_id=tenant_id, category="attendance")
    assert notes.count() == 1
    assert notes.first().recipient_email == "p3@example.com"


@pytest.mark.django_db(transaction=True)
def test_nothing_is_sent_if_the_roll_never_commits(tenant_id, klass):
    """
    The duty-of-care bug the on_commit hook exists to prevent: a parent told
    their child is absent when the mark was rolled back and does not exist.
    """
    from products.cyed.attendance import services

    section, students = klass
    try:
        with transaction.atomic():
            services.take_roll(
                tenant_id=tenant_id, class_section_id=section.id, date="2026-08-11",
                marks=[{"student": str(students[1].id), "status": "absent"}],
            )
            raise RuntimeError("something later in the request failed")
    except RuntimeError:
        pass

    assert AttendanceMark.objects.filter(tenant_id=tenant_id).count() == 0
    assert Notification.objects.filter(tenant_id=tenant_id, category="attendance").count() == 0


# ── validation ───────────────────────────────────────────────────────────────
@pytest.mark.django_db
def test_marking_a_student_who_is_not_in_the_class_is_refused(teacher_client, tenant_id, klass):
    """Otherwise a wrong class id writes attendance against lessons a child never attends."""
    section, _ = klass
    stranger = Student.objects.create(
        tenant_id=tenant_id, first_name="Not", last_name="Here", year_level=9
    )
    resp = _take(teacher_client, section, marks=[{"student": str(stranger.id), "status": "absent"}])
    assert resp.status_code == 400
    assert "not enrolled in this class section" in resp.data["detail"]
    assert AttendanceMark.objects.filter(tenant_id=tenant_id).count() == 0


@pytest.mark.django_db
def test_a_student_listed_twice_is_refused(teacher_client, klass):
    """Silently picking one of two conflicting statuses is not software's call."""
    section, students = klass
    resp = _take(teacher_client, section, marks=[
        {"student": str(students[0].id), "status": "absent"},
        {"student": str(students[0].id), "status": "present"},
    ])
    assert resp.status_code == 400
    assert "appears twice" in resp.data["detail"]


@pytest.mark.django_db
def test_invalid_status_is_refused(teacher_client, klass):
    section, students = klass
    resp = _take(teacher_client, section, marks=[{"student": str(students[0].id), "status": "maybe"}])
    assert resp.status_code == 400
    assert "not a valid attendance status" in resp.data["detail"]


@pytest.mark.django_db
def test_negative_minutes_late_is_refused(teacher_client, klass):
    section, students = klass
    resp = _take(teacher_client, section, marks=[
        {"student": str(students[0].id), "status": "late", "minutes_late": -5},
    ])
    assert resp.status_code == 400


@pytest.mark.django_db
def test_empty_class_is_refused_rather_than_silently_recording_nothing(teacher_client, tenant_id):
    empty = ClassSection.objects.create(tenant_id=tenant_id, name="Ghost Class", year_level=9)
    resp = _take(teacher_client, empty)
    assert resp.status_code == 400
    assert "no roll to take" in resp.data["detail"]


# ── roster view ──────────────────────────────────────────────────────────────
@pytest.mark.django_db
def test_roster_shows_who_is_marked_and_who_is_not(teacher_client, tenant_id, klass):
    section, students = klass
    taken = _take(teacher_client, section, marks=[{"student": str(students[1].id), "status": "absent"}])
    roll_call_id = taken.data["roll_call"]

    resp = teacher_client.get(f"/api/v1/attendance/roll-calls/{roll_call_id}/roster/")
    assert resp.status_code == 200
    assert resp.data["count"] == 5
    assert all(row["marked"] for row in resp.data["students"])
    absent = [r for r in resp.data["students"] if r["status"] == "absent"]
    assert len(absent) == 1
