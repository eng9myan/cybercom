"""
Exam operations: seating, hall tickets, registers.

The rules that matter are the ones exam supervision turns on — capacity is a
hard limit, one student to a seat, and access arrangements are placed first
rather than squeezed in afterwards.
"""

import uuid
from datetime import date

import pytest
from rest_framework.test import APIClient

from products.cyed.exams import services
from products.cyed.exams.models import ExamCandidate, ExamRoom, ExamRoomAllocation, ExamSitting
from products.cyed.sis.models import ClassSection, Enrolment, Student

EXAM_DAY = date(2026, 11, 12)


@pytest.fixture
def client_for(mint_token, mock_jwks, tenant_id):
    def _make(roles, email="exams@cyed.edu.au"):
        c = APIClient()
        c.credentials(HTTP_AUTHORIZATION=f"Bearer {mint_token({
            'sub': str(uuid.uuid4()), 'email': email, 'tenant_id': str(tenant_id),
            'realm_access': {'roles': roles},
        })}")
        return c
    return _make


@pytest.fixture
def staff(client_for):
    return client_for(["tenant_admin"])


@pytest.fixture
def cohort(tenant_id):
    section = ClassSection.objects.create(tenant_id=tenant_id, name="10A English", year_level=10)
    students = []
    for i, name in enumerate(["Ana", "Ben", "Cara", "Dev", "Eve", "Finn"]):
        s = Student.objects.create(
            tenant_id=tenant_id, first_name=name, last_name=f"S{i}",
            year_level=10, enrolment_status="enrolled", student_number=f"S{1000 + i}",
        )
        Enrolment.objects.create(
            tenant_id=tenant_id, student=s, class_section=section, status="active"
        )
        students.append(s)
    return section, students


@pytest.fixture
def sitting(tenant_id):
    return ExamSitting.objects.create(
        tenant_id=tenant_id, name="Year 10 English", subject="English", year_level=10,
        date=EXAM_DAY, start_time="09:00:00", duration_minutes=90,
        materials_permitted="Pen, dictionary",
    )


@pytest.fixture
def hall(tenant_id):
    return ExamRoom.objects.create(
        tenant_id=tenant_id, name="Main Hall", capacity=8, rows=2, columns=4
    )


# ── entering candidates ──────────────────────────────────────────────────────
@pytest.mark.django_db
def test_a_whole_class_can_be_entered_at_once(staff, sitting, cohort):
    section, students = cohort
    resp = staff.post(f"/api/v1/exams/sittings/{sitting.id}/enter-cohort/", {
        "class_section": str(section.id),
    }, format="json")
    assert resp.status_code == 201, resp.data
    assert resp.data["entered"] == len(students)


@pytest.mark.django_db
def test_entering_twice_does_not_duplicate(staff, sitting, cohort):
    section, students = cohort
    staff.post(f"/api/v1/exams/sittings/{sitting.id}/enter-cohort/",
               {"class_section": str(section.id)}, format="json")
    again = staff.post(f"/api/v1/exams/sittings/{sitting.id}/enter-cohort/",
                       {"class_section": str(section.id)}, format="json")
    assert again.data["entered"] == 0
    assert again.data["already_entered"] == len(students)
    assert sitting.candidates.count() == len(students)


# ── seating ──────────────────────────────────────────────────────────────────
@pytest.mark.django_db
def test_seating_places_everyone_once(staff, tenant_id, sitting, cohort, hall):
    section, students = cohort
    staff.post(f"/api/v1/exams/sittings/{sitting.id}/enter-cohort/",
               {"class_section": str(section.id)}, format="json")
    ExamRoomAllocation.objects.create(tenant_id=tenant_id, sitting=sitting, room=hall)

    resp = staff.post(f"/api/v1/exams/sittings/{sitting.id}/allocate-seats/", {}, format="json")
    assert resp.status_code == 200, resp.data
    assert resp.data["seated"] == len(students)

    seats = list(ExamCandidate.objects.filter(sitting=sitting).values_list("seat_label", flat=True))
    assert len(seats) == len(set(seats))     # nobody shares a desk
    assert all(seats)


@pytest.mark.django_db
def test_not_enough_desks_refuses_rather_than_seating_some(staff, tenant_id, sitting, cohort):
    """A plan that silently leaves students unplaced is worse than no plan."""
    section, _students = cohort
    small = ExamRoom.objects.create(
        tenant_id=tenant_id, name="Tiny Room", capacity=2, rows=1, columns=2
    )
    staff.post(f"/api/v1/exams/sittings/{sitting.id}/enter-cohort/",
               {"class_section": str(section.id)}, format="json")
    ExamRoomAllocation.objects.create(tenant_id=tenant_id, sitting=sitting, room=small)

    resp = staff.post(f"/api/v1/exams/sittings/{sitting.id}/allocate-seats/", {}, format="json")
    assert resp.status_code == 409
    assert "Book another room" in resp.data["detail"]
    assert ExamCandidate.objects.filter(sitting=sitting).exclude(seat_label="").count() == 0


@pytest.mark.django_db
def test_seating_with_no_room_booked_is_refused(staff, sitting, cohort):
    section, _ = cohort
    staff.post(f"/api/v1/exams/sittings/{sitting.id}/enter-cohort/",
               {"class_section": str(section.id)}, format="json")
    resp = staff.post(f"/api/v1/exams/sittings/{sitting.id}/allocate-seats/", {}, format="json")
    assert resp.status_code == 409
    assert "Book at least one room" in resp.data["detail"]


@pytest.mark.django_db
def test_access_arrangements_are_seated_first_and_in_an_accessible_room(
    staff, tenant_id, sitting, cohort, hall
):
    """
    Seating an arrangement last means seating it wherever is left — which is
    how a child with an entitlement ends up without it.
    """
    section, students = cohort
    accessible = ExamRoom.objects.create(
        tenant_id=tenant_id, name="Accessible Room", capacity=4, rows=1, columns=4,
        is_accessible=True,
    )
    staff.post(f"/api/v1/exams/sittings/{sitting.id}/enter-cohort/",
               {"class_section": str(section.id)}, format="json")
    ExamRoomAllocation.objects.create(tenant_id=tenant_id, sitting=sitting, room=hall)
    ExamRoomAllocation.objects.create(tenant_id=tenant_id, sitting=sitting, room=accessible)

    # Finn sorts last alphabetically, so without the arrangement rule he would
    # be placed last, in whatever room was left.
    ExamCandidate.objects.filter(sitting=sitting, student=students[5]).update(
        access_arrangement="separate_room", extra_time_minutes=30
    )
    staff.post(f"/api/v1/exams/sittings/{sitting.id}/allocate-seats/", {}, format="json")

    candidate = ExamCandidate.objects.get(sitting=sitting, student=students[5])
    assert candidate.room.is_accessible is True


@pytest.mark.django_db
def test_reallocating_is_deterministic(staff, tenant_id, sitting, cohort, hall):
    """A chart printed on Tuesday must still match the hall on Thursday."""
    section, _ = cohort
    staff.post(f"/api/v1/exams/sittings/{sitting.id}/enter-cohort/",
               {"class_section": str(section.id)}, format="json")
    ExamRoomAllocation.objects.create(tenant_id=tenant_id, sitting=sitting, room=hall)

    staff.post(f"/api/v1/exams/sittings/{sitting.id}/allocate-seats/", {}, format="json")
    first = dict(ExamCandidate.objects.filter(sitting=sitting).values_list("student_id", "seat_label"))

    staff.post(f"/api/v1/exams/sittings/{sitting.id}/allocate-seats/", {}, format="json")
    second = dict(ExamCandidate.objects.filter(sitting=sitting).values_list("student_id", "seat_label"))
    assert first == second


@pytest.mark.django_db
def test_a_room_cannot_claim_more_seats_than_its_grid(staff, tenant_id):
    resp = staff.post("/api/v1/exams/rooms/", {
        "name": "Impossible", "capacity": 50, "rows": 2, "columns": 4,
    }, format="json")
    assert resp.status_code == 400
    assert "cannot" in str(resp.data)


# ── hall tickets ─────────────────────────────────────────────────────────────
@pytest.mark.django_db
def test_tickets_cannot_be_issued_before_seating(staff, tenant_id, sitting, cohort, hall):
    """A ticket issued before allocation would name a seat that then changes."""
    section, _ = cohort
    staff.post(f"/api/v1/exams/sittings/{sitting.id}/enter-cohort/",
               {"class_section": str(section.id)}, format="json")
    ExamRoomAllocation.objects.create(tenant_id=tenant_id, sitting=sitting, room=hall)

    resp = staff.post(f"/api/v1/exams/sittings/{sitting.id}/issue-tickets/", {}, format="json")
    assert resp.status_code == 409
    assert "Allocate seating" in resp.data["detail"]


@pytest.mark.django_db
def test_a_ticket_carries_seat_room_and_finish_time(staff, tenant_id, sitting, cohort, hall):
    section, students = cohort
    staff.post(f"/api/v1/exams/sittings/{sitting.id}/enter-cohort/",
               {"class_section": str(section.id)}, format="json")
    ExamRoomAllocation.objects.create(tenant_id=tenant_id, sitting=sitting, room=hall)
    ExamCandidate.objects.filter(sitting=sitting, student=students[0]).update(
        access_arrangement="extra_time", extra_time_minutes=15
    )
    staff.post(f"/api/v1/exams/sittings/{sitting.id}/allocate-seats/", {}, format="json")
    staff.post(f"/api/v1/exams/sittings/{sitting.id}/issue-tickets/", {}, format="json")

    candidate = ExamCandidate.objects.get(sitting=sitting, student=students[0])
    resp = staff.get(f"/api/v1/exams/candidates/{candidate.id}/ticket/")
    assert resp.status_code == 200
    assert resp.data["room"] == "Main Hall"
    assert resp.data["seat"]
    assert resp.data["duration_minutes"] == 105        # 90 + 15 extra time
    assert resp.data["finish_time"] == "10:45:00"
    assert resp.data["materials_permitted"] == "Pen, dictionary"


@pytest.mark.django_db
def test_a_student_can_read_their_own_ticket_and_not_anothers(
    staff, client_for, tenant_id, sitting, cohort, hall
):
    section, students = cohort
    students[0].email = "ana@student.cyed.edu.au"
    students[0].save(update_fields=["email"])
    staff.post(f"/api/v1/exams/sittings/{sitting.id}/enter-cohort/",
               {"class_section": str(section.id)}, format="json")
    ExamRoomAllocation.objects.create(tenant_id=tenant_id, sitting=sitting, room=hall)
    staff.post(f"/api/v1/exams/sittings/{sitting.id}/allocate-seats/", {}, format="json")
    staff.post(f"/api/v1/exams/sittings/{sitting.id}/issue-tickets/", {}, format="json")

    pupil = client_for(["student"], "ana@student.cyed.edu.au")
    mine = ExamCandidate.objects.get(sitting=sitting, student=students[0])
    theirs = ExamCandidate.objects.get(sitting=sitting, student=students[1])

    assert pupil.get(f"/api/v1/exams/candidates/{mine.id}/ticket/").status_code == 200
    assert pupil.get(f"/api/v1/exams/candidates/{theirs.id}/ticket/").status_code == 404


@pytest.mark.django_db
def test_seats_cannot_be_hand_edited(staff, tenant_id, sitting, cohort, hall):
    """A hand-edited seat is how two students end up at one desk."""
    section, students = cohort
    staff.post(f"/api/v1/exams/sittings/{sitting.id}/enter-cohort/",
               {"class_section": str(section.id)}, format="json")
    ExamRoomAllocation.objects.create(tenant_id=tenant_id, sitting=sitting, room=hall)
    staff.post(f"/api/v1/exams/sittings/{sitting.id}/allocate-seats/", {}, format="json")

    a, b = ExamCandidate.objects.filter(sitting=sitting)[:2]
    staff.patch(f"/api/v1/exams/candidates/{a.id}/", {"seat_label": b.seat_label}, format="json")
    a.refresh_from_db()
    assert a.seat_label != b.seat_label


# ── the day itself ───────────────────────────────────────────────────────────
@pytest.mark.django_db
def test_seating_chart_groups_by_room_with_arrangements_visible(
    staff, tenant_id, sitting, cohort, hall
):
    section, students = cohort
    staff.post(f"/api/v1/exams/sittings/{sitting.id}/enter-cohort/",
               {"class_section": str(section.id)}, format="json")
    ExamRoomAllocation.objects.create(tenant_id=tenant_id, sitting=sitting, room=hall)
    ExamCandidate.objects.filter(sitting=sitting, student=students[2]).update(
        access_arrangement="rest_breaks"
    )
    staff.post(f"/api/v1/exams/sittings/{sitting.id}/allocate-seats/", {}, format="json")

    resp = staff.get(f"/api/v1/exams/sittings/{sitting.id}/seating-chart/")
    assert resp.status_code == 200
    assert resp.data["unseated"] == 0
    room = resp.data["rooms"][0]
    assert room["seated"] == len(students)
    assert any(s["access_arrangement"] == "rest_breaks" for s in room["seats"])


@pytest.mark.django_db
def test_register_counts_who_turned_up(staff, tenant_id, sitting, cohort, hall):
    section, students = cohort
    staff.post(f"/api/v1/exams/sittings/{sitting.id}/enter-cohort/",
               {"class_section": str(section.id)}, format="json")
    ExamRoomAllocation.objects.create(tenant_id=tenant_id, sitting=sitting, room=hall)
    staff.post(f"/api/v1/exams/sittings/{sitting.id}/allocate-seats/", {}, format="json")

    absent = ExamCandidate.objects.get(sitting=sitting, student=students[3])
    staff.post(f"/api/v1/exams/candidates/{absent.id}/mark-attendance/",
               {"attendance": "absent"}, format="json")

    resp = staff.get(f"/api/v1/exams/sittings/{sitting.id}/register/")
    assert resp.data["by_status"]["absent"] == 1
    assert resp.data["by_status"]["expected"] == len(students) - 1
