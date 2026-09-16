"""
Emergency roll and medical action plans.

These are the two safety-critical features in the product. The tests below are
mostly about the ways a roll can be confidently wrong — defaulting people to
safe, counting children who are at home, or losing a medical alert at the
moment someone is missing.
"""

import uuid

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from products.cyed.attendance.models import EmergencyDrill, EmergencyRollEntry
from products.cyed.health.models import ActionPlan
from products.cyed.sis.models import ClassSection, Enrolment, Student
from products.cyed.visitors.models import Visitor

TODAY = timezone.localdate()


@pytest.fixture
def client_for(mint_token, mock_jwks, tenant_id):
    def _make(roles, email="office@cyed.edu.au"):
        c = APIClient()
        c.credentials(HTTP_AUTHORIZATION=f"Bearer {mint_token({
            'sub': str(uuid.uuid4()), 'email': email, 'tenant_id': str(tenant_id),
            'realm_access': {'roles': roles},
        })}")
        return c
    return _make


@pytest.fixture
def office(client_for):
    return client_for(["tenant_admin"])


@pytest.fixture
def school(tenant_id):
    section = ClassSection.objects.create(tenant_id=tenant_id, name="8A", year_level=8)
    students = []
    for name in ["Ana", "Ben", "Cara", "Dev"]:
        s = Student.objects.create(
            tenant_id=tenant_id, first_name=name, last_name="Tran",
            year_level=8, enrolment_status="enrolled",
        )
        Enrolment.objects.create(
            tenant_id=tenant_id, student=s, class_section=section, status="active"
        )
        students.append(s)
    return section, students


def _take_roll(client, section, students, absent=()):
    return client.post("/api/v1/attendance/roll-calls/take/", {
        "class_section": str(section.id),
        "date": TODAY.isoformat(),
        "marks": [{"student": str(s.id), "status": "absent"} for s in absent],
    }, format="json")


# ── who is on site ───────────────────────────────────────────────────────────
@pytest.mark.django_db
def test_the_roll_counts_who_is_here_not_who_is_enrolled(office, school):
    """
    A student marked absent this morning is at home, not missing. Listing them
    as unaccounted sends someone back into a building for nothing.
    """
    section, students = school
    _take_roll(office, section, students, absent=[students[3]])

    resp = office.get("/api/v1/attendance/emergency-drills/on-site/")
    assert resp.status_code == 200
    assert resp.data["on_site_count"] == 3
    assert resp.data["off_site_count"] == 1


@pytest.mark.django_db
def test_signed_in_visitors_are_on_the_roll(office, tenant_id, school):
    """A warden counting only students comes up short and cannot say why."""
    section, students = school
    _take_roll(office, section, students)
    Visitor.objects.create(
        tenant_id=tenant_id, full_name="Sam Contractor", organisation="Acme Roofing",
        purpose="Gutter repair", signed_in_at=timezone.now(),
    )
    Visitor.objects.create(
        tenant_id=tenant_id, full_name="Gone Already", signed_in_at=timezone.now(),
        signed_out_at=timezone.now(),
    )

    resp = office.get("/api/v1/attendance/emergency-drills/on-site/")
    assert [v["name"] for v in resp.data["visitors"]] == ["Sam Contractor"]


@pytest.mark.django_db
def test_students_are_grouped_by_the_class_a_teacher_supervises(office, school):
    section, students = school
    _take_roll(office, section, students)
    resp = office.get("/api/v1/attendance/emergency-drills/on-site/")
    assert resp.data["sections"][0]["class_section"] == "8A"
    assert resp.data["sections"][0]["count"] == 4


# ── medical alerts ───────────────────────────────────────────────────────────
@pytest.mark.django_db
def test_a_medical_alert_travels_with_the_roll(office, tenant_id, school):
    section, students = school
    ActionPlan.objects.create(
        tenant_id=tenant_id, student=students[0], plan_type="anaphylaxis",
        severity="critical", triggers="Peanuts, tree nuts",
        emergency_steps="1. Lay flat. 2. EpiPen to outer thigh. 3. Call 000.",
        medication="EpiPen Jr 150mcg", medication_location="Front office, red box",
        review_due=TODAY + timezone.timedelta(days=200),
    )
    _take_roll(office, section, students)

    resp = office.get("/api/v1/attendance/emergency-drills/on-site/")
    assert resp.data["medical_alerts"] == 1
    flagged = [
        s for section_row in resp.data["sections"]
        for s in section_row["students"] if "medical_alert" in s
    ]
    assert flagged[0]["medical_alert"]["type"] == "Anaphylaxis"
    assert flagged[0]["medical_alert"]["medication_location"] == "Front office, red box"


# ── running a drill ──────────────────────────────────────────────────────────
@pytest.mark.django_db
def test_opening_a_drill_freezes_the_roll(office, tenant_id, school):
    """
    The roll must not shift under the people using it because a late student
    was marked present halfway through an evacuation.
    """
    section, students = school
    _take_roll(office, section, students, absent=[students[3]])

    opened = office.post("/api/v1/attendance/emergency-drills/open/",
                         {"kind": "fire_drill"}, format="json")
    assert opened.status_code == 201, opened.data
    assert opened.data["expected"] == 3

    # A student arriving after the alarm does not change the frozen roll.
    office.post("/api/v1/attendance/roll-calls/take/", {
        "class_section": str(section.id), "date": TODAY.isoformat(),
        "marks": [{"student": str(students[3].id), "status": "late"}],
    }, format="json")

    board = office.get(f"/api/v1/attendance/emergency-drills/{opened.data['drill']}/board/")
    assert board.data["expected"] == 3


@pytest.mark.django_db
def test_everyone_starts_unaccounted_for(office, school):
    """
    A roll that defaults to safe produces a clean board and a wrong one. The
    whole value is knowing precisely who has not been seen.
    """
    section, students = school
    _take_roll(office, section, students)
    opened = office.post("/api/v1/attendance/emergency-drills/open/", {}, format="json")

    assert opened.data["safe"] == 0
    assert opened.data["unaccounted"] == 4
    assert opened.data["all_clear"] is False


@pytest.mark.django_db
def test_marking_students_safe_clears_the_board(office, school):
    section, students = school
    _take_roll(office, section, students)
    drill = office.post("/api/v1/attendance/emergency-drills/open/", {}, format="json").data["drill"]

    resp = office.post(f"/api/v1/attendance/emergency-drills/{drill}/account-for/", {
        "students": [str(s.id) for s in students], "state": "safe",
    }, format="json")

    assert resp.data["updated"] == 4
    assert resp.data["safe"] == 4
    assert resp.data["all_clear"] is True


@pytest.mark.django_db
def test_calling_the_same_student_twice_is_harmless(office, school):
    """A noisy assembly point produces duplicate calls; erroring would be useless."""
    section, students = school
    _take_roll(office, section, students)
    drill = office.post("/api/v1/attendance/emergency-drills/open/", {}, format="json").data["drill"]

    body = {"students": [str(students[0].id)], "state": "safe"}
    office.post(f"/api/v1/attendance/emergency-drills/{drill}/account-for/", body, format="json")
    second = office.post(
        f"/api/v1/attendance/emergency-drills/{drill}/account-for/", body, format="json"
    )
    assert second.status_code == 200
    assert second.data["safe"] == 1


@pytest.mark.django_db
def test_students_with_a_medical_alert_head_the_missing_list(office, tenant_id, school):
    """
    If someone is missing and carries an EpiPen, that is who the next person
    out the door should be looking for.
    """
    section, students = school
    ActionPlan.objects.create(
        tenant_id=tenant_id, student=students[3], plan_type="anaphylaxis",
        severity="critical", emergency_steps="EpiPen.", medication="EpiPen",
        medication_location="Office",
    )
    _take_roll(office, section, students)
    drill = office.post("/api/v1/attendance/emergency-drills/open/", {}, format="json").data["drill"]

    # Everyone accounted for except two, one of whom has the alert.
    office.post(f"/api/v1/attendance/emergency-drills/{drill}/account-for/", {
        "students": [str(students[0].id), str(students[1].id)], "state": "safe",
    }, format="json")

    board = office.get(f"/api/v1/attendance/emergency-drills/{drill}/board/")
    assert board.data["unaccounted"] == 2
    assert board.data["still_unaccounted"][0]["medical_alert"] is True


@pytest.mark.django_db
def test_a_drill_can_be_closed_with_people_missing_but_the_count_is_kept(office, school):
    """An evacuation does not wait for tidy data; the debrief must not lose it."""
    section, students = school
    _take_roll(office, section, students)
    drill_id = office.post(
        "/api/v1/attendance/emergency-drills/open/", {}, format="json"
    ).data["drill"]

    office.post(f"/api/v1/attendance/emergency-drills/{drill_id}/account-for/", {
        "students": [str(students[0].id)], "state": "safe",
    }, format="json")
    closed = office.post(f"/api/v1/attendance/emergency-drills/{drill_id}/close/", {
        "note": "Two students found at the far gate after the all-clear.",
    }, format="json")

    assert closed.status_code == 200
    drill = EmergencyDrill.objects.get(id=drill_id)
    assert drill.unaccounted_at_close == 3
    assert drill.ended_at is not None


@pytest.mark.django_db
def test_a_closed_drill_cannot_be_edited(office, school):
    section, students = school
    _take_roll(office, section, students)
    drill = office.post("/api/v1/attendance/emergency-drills/open/", {}, format="json").data["drill"]
    office.post(f"/api/v1/attendance/emergency-drills/{drill}/close/", {}, format="json")

    resp = office.post(f"/api/v1/attendance/emergency-drills/{drill}/account-for/", {
        "students": [str(students[0].id)], "state": "safe",
    }, format="json")
    assert resp.status_code == 409


@pytest.mark.django_db
def test_a_drill_cannot_be_created_by_posting_a_bare_row(office, school):
    """That path would skip the roll snapshot entirely."""
    resp = office.post("/api/v1/attendance/emergency-drills/", {"kind": "fire_drill"}, format="json")
    assert resp.status_code == 405
    assert EmergencyDrill.objects.count() == 0


@pytest.mark.django_db
def test_the_emergency_roll_is_staff_only(client_for, school):
    parent = client_for(["parent"], "p@example.com")
    assert parent.get("/api/v1/attendance/emergency-drills/on-site/").status_code == 403
