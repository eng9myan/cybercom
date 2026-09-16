import uuid
from datetime import date

import pytest
from rest_framework.test import APIClient

from products.cyed.attendance.models import AttendanceMark, RollCall
from products.cyed.notifications.models import Notification
from products.cyed.sis.models import ClassSection, Guardian, Student


@pytest.fixture
def client_for(mint_token, mock_jwks, tenant_id):
    def _make(roles, email="user@cyed.edu.au"):
        token = mint_token(
            {"sub": str(uuid.uuid4()), "email": email, "tenant_id": str(tenant_id),
             "realm_access": {"roles": roles}}
        )
        c = APIClient()
        c.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        return c
    return _make


def _student_with_guardian(tenant_id, guardian_email="parent@home.com"):
    student = Student.objects.create(tenant_id=tenant_id, first_name="Minh", last_name="Nguyen", year_level=8,
                                     email="minh@student.cyed.edu.au")
    guardian = Guardian.objects.create(tenant_id=tenant_id, first_name="Jia", last_name="Nguyen",
                                       email=guardian_email, phone="0400000000")
    guardian.students.add(student)
    return student, guardian


def _mark_absent(callbacks, **kwargs):
    """
    Record a mark and run the resulting commit hooks.

    Guardian alerts are dispatched from `transaction.on_commit` so that a
    request which fails later cannot tell a parent their child is absent when
    no such mark exists. In a test the surrounding transaction is rolled back
    and never commits, so the hooks have to be run explicitly — that is what
    `django_capture_on_commit_callbacks(execute=True)` does.
    """
    with callbacks(execute=True):
        return AttendanceMark.objects.create(**kwargs)


@pytest.mark.django_db
def test_absent_mark_triggers_guardian_notification(tenant_id, django_capture_on_commit_callbacks):
    student, guardian = _student_with_guardian(tenant_id)
    section = ClassSection.objects.create(tenant_id=tenant_id, name="8A", year_level=8)
    roll = RollCall.objects.create(tenant_id=tenant_id, class_section=section, date=date.today())

    _mark_absent(
        django_capture_on_commit_callbacks,
        tenant_id=tenant_id, roll_call=roll, student=student, status="absent",
    )

    notifs = Notification.objects.filter(tenant_id=tenant_id, category="attendance")
    assert notifs.count() == 1
    n = notifs.first()
    assert n.recipient_email == "parent@home.com"
    assert n.status == "sent"  # in-app delivered immediately
    assert "absent" in n.body


@pytest.mark.django_db
def test_present_mark_does_not_notify(tenant_id):
    student, _ = _student_with_guardian(tenant_id)
    section = ClassSection.objects.create(tenant_id=tenant_id, name="8A", year_level=8)
    roll = RollCall.objects.create(tenant_id=tenant_id, class_section=section, date=date.today())
    AttendanceMark.objects.create(tenant_id=tenant_id, roll_call=roll, student=student, status="present")
    assert Notification.objects.filter(tenant_id=tenant_id).count() == 0


@pytest.mark.django_db
def test_parent_sees_only_own_notifications(
    client_for, tenant_id, django_capture_on_commit_callbacks
):
    student, _ = _student_with_guardian(tenant_id, guardian_email="parent@home.com")
    section = ClassSection.objects.create(tenant_id=tenant_id, name="8A", year_level=8)
    roll = RollCall.objects.create(tenant_id=tenant_id, class_section=section, date=date.today())
    _mark_absent(
        django_capture_on_commit_callbacks,
        tenant_id=tenant_id, roll_call=roll, student=student, status="late",
    )

    # A notification for someone else's child.
    other, _ = _student_with_guardian(tenant_id, guardian_email="someone.else@home.com")
    roll2 = RollCall.objects.create(tenant_id=tenant_id, class_section=section, date=date.today(), period_label="P2")
    _mark_absent(
        django_capture_on_commit_callbacks,
        tenant_id=tenant_id, roll_call=roll2, student=other, status="absent",
    )

    parent = client_for(["parent"], email="parent@home.com")
    resp = parent.get("/api/v1/notifications/")
    rows = resp.data["results"] if isinstance(resp.data, dict) else resp.data
    assert len(rows) == 1
    assert rows[0]["recipient_email"] == "parent@home.com"


@pytest.mark.django_db
def test_mark_read(client_for, tenant_id, django_capture_on_commit_callbacks):
    student, _ = _student_with_guardian(tenant_id, guardian_email="parent@home.com")
    section = ClassSection.objects.create(tenant_id=tenant_id, name="8A", year_level=8)
    roll = RollCall.objects.create(tenant_id=tenant_id, class_section=section, date=date.today())
    _mark_absent(
        django_capture_on_commit_callbacks,
        tenant_id=tenant_id, roll_call=roll, student=student, status="absent",
    )
    n = Notification.objects.filter(tenant_id=tenant_id).first()

    parent = client_for(["parent"], email="parent@home.com")
    resp = parent.post(f"/api/v1/notifications/{n.id}/mark_read/")
    assert resp.status_code == 200
    assert resp.data["status"] == "read"


@pytest.mark.django_db
def test_announcement_is_staff_only(client_for, tenant_id):
    _student_with_guardian(tenant_id, guardian_email="parent@home.com")

    parent = client_for(["parent"], email="parent@home.com")
    assert parent.post("/api/v1/notifications/announce/", {"subject": "Hi"}, format="json").status_code == 403

    admin = client_for(["tenant_admin"])
    resp = admin.post("/api/v1/notifications/announce/",
                      {"subject": "School closed Friday", "body": "Pupil-free day."}, format="json")
    assert resp.status_code == 201
    assert resp.data["created"] == 1
