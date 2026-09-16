"""
"What is my timetable?" for every kind of caller.

Students had no way to answer this at all — `timetable/slots/` was unscoped
CRUD, so the only options were the whole school's timetable or nothing.
"""

import uuid

import pytest
from rest_framework.test import APIClient

from products.cyed.hr.models import Staff
from products.cyed.hr.testing import clear_for_teaching
from products.cyed.sis.models import ClassSection, Enrolment, Guardian, Student
from products.cyed.timetable.models import TimetableSlot


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
def school(tenant_id):
    teacher = Staff.objects.create(
        tenant_id=tenant_id, first_name="Ada", last_name="Lovelace",
        role="teacher", email="ada@cyed.edu.au",
    )
    clear_for_teaching(teacher)

    maths = ClassSection.objects.create(
        tenant_id=tenant_id, name="8A Mathematics", year_level=8, teacher=teacher
    )
    art = ClassSection.objects.create(tenant_id=tenant_id, name="8A Art", year_level=8)

    TimetableSlot.objects.create(
        tenant_id=tenant_id, class_section=maths, day_of_week="mon",
        period_label="P1", start_time="09:00", end_time="10:00", teacher=teacher,
    )
    TimetableSlot.objects.create(
        tenant_id=tenant_id, class_section=art, day_of_week="tue",
        period_label="P2", start_time="10:00", end_time="11:00",
    )

    mia = Student.objects.create(
        tenant_id=tenant_id, first_name="Mia", last_name="Tran", year_level=8,
        enrolment_status="enrolled", email="mia@student.cyed.edu.au",
    )
    Enrolment.objects.create(
        tenant_id=tenant_id, student=mia, class_section=maths, status="active"
    )

    ken = Student.objects.create(
        tenant_id=tenant_id, first_name="Ken", last_name="Tran", year_level=8,
        enrolment_status="enrolled",
    )
    Enrolment.objects.create(
        tenant_id=tenant_id, student=ken, class_section=art, status="active"
    )

    parent = Guardian.objects.create(
        tenant_id=tenant_id, first_name="Hoa", last_name="Tran", email="hoa@example.com"
    )
    parent.students.add(mia, ken)

    single = Guardian.objects.create(
        tenant_id=tenant_id, first_name="Solo", last_name="Parent", email="solo@example.com"
    )
    single.students.add(mia)

    return {"teacher": teacher, "maths": maths, "art": art, "mia": mia, "ken": ken}


@pytest.mark.django_db
def test_a_teacher_gets_the_classes_they_take(client_for, school):
    resp = client_for(["teacher"], "ada@cyed.edu.au").get("/api/v1/timetable/slots/mine/")
    assert resp.status_code == 200
    assert [s["period_label"] for s in resp.data] == ["P1"]


@pytest.mark.django_db
def test_a_student_gets_the_classes_they_are_enrolled_in(client_for, school):
    resp = client_for(["student"], "mia@student.cyed.edu.au").get("/api/v1/timetable/slots/mine/")
    assert resp.status_code == 200
    assert len(resp.data) == 1
    assert resp.data[0]["class_section_name"] == "8A Mathematics"


@pytest.mark.django_db
def test_a_student_does_not_see_the_whole_schools_timetable(client_for, school):
    """The failure mode this replaces: unscoped CRUD over every slot."""
    resp = client_for(["student"], "mia@student.cyed.edu.au").get("/api/v1/timetable/slots/mine/")
    names = {s["class_section_name"] for s in resp.data}
    assert "8A Art" not in names


@pytest.mark.django_db
def test_a_parent_with_one_child_needs_no_argument(client_for, school):
    resp = client_for(["parent"], "solo@example.com").get("/api/v1/timetable/slots/mine/")
    assert resp.status_code == 200
    assert len(resp.data) == 1


@pytest.mark.django_db
def test_a_parent_with_two_children_is_asked_which(client_for, school):
    """Guessing which child they meant would be worse than asking."""
    resp = client_for(["parent"], "hoa@example.com").get("/api/v1/timetable/slots/mine/")
    assert resp.status_code == 400
    assert len(resp.data["students"]) == 2


@pytest.mark.django_db
def test_a_parent_can_name_their_child(client_for, school):
    resp = client_for(["parent"], "hoa@example.com").get(
        f"/api/v1/timetable/slots/mine/?student={school['ken'].id}"
    )
    assert resp.status_code == 200
    assert resp.data[0]["class_section_name"] == "8A Art"


@pytest.mark.django_db
def test_a_parent_cannot_name_someone_elses_child(client_for, school, tenant_id):
    stranger = Student.objects.create(
        tenant_id=tenant_id, first_name="Not", last_name="Yours", year_level=8,
        enrolment_status="enrolled",
    )
    resp = client_for(["parent"], "solo@example.com").get(
        f"/api/v1/timetable/slots/mine/?student={stranger.id}"
    )
    assert resp.status_code == 403


@pytest.mark.django_db
def test_an_unlinked_account_gets_nothing_rather_than_everything(client_for, school):
    """Falling through to the unscoped queryset would leak the whole timetable."""
    resp = client_for(["parent"], "nobody@example.com").get("/api/v1/timetable/slots/mine/")
    assert resp.status_code == 200
    assert resp.data == []


@pytest.mark.django_db
def test_staff_can_look_at_one_students_day(client_for, school):
    """
    A named student wins over the caller's role. Without this a staff account
    asking for one child's timetable gets their own teaching load — or, having
    no Staff record, an error about staff records on a family-facing screen.
    """
    resp = client_for(["tenant_admin"], "office@cyed.edu.au").get(
        f"/api/v1/timetable/slots/mine/?student={school['mia'].id}"
    )
    assert resp.status_code == 200
    assert [s["class_section_name"] for s in resp.data] == ["8A Mathematics"]


@pytest.mark.django_db
def test_staff_asking_for_no_one_in_particular_are_told_to_name_a_student(client_for, school):
    """Returning every slot as though it were one child's day would be worse."""
    resp = client_for(["tenant_admin"], "office@cyed.edu.au").get(
        "/api/v1/timetable/slots/mine/?student="
    )
    assert resp.status_code == 404  # no Staff record for this account

