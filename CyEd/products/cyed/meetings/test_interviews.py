"""
Parent–teacher interview booking.

Most of these guard fairness and the promise that a booked appointment exists:
one booking per slot under a race, a per-family cap, and no booking outside the
round's window.
"""

import uuid
from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from products.cyed.hr.models import Staff
from products.cyed.meetings import interviews
from products.cyed.meetings.models import InterviewBooking, InterviewRound, InterviewSlot
from products.cyed.sis.models import Guardian, Student

NOW = timezone.now()


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
def other_parent(client_for):
    return client_for(["parent"], "yui@example.com")


@pytest.fixture
def school(tenant_id):
    teachers = [
        Staff.objects.create(
            tenant_id=tenant_id, first_name=n, last_name="Teacher",
            role="teacher", email=f"{n.lower()}@cyed.edu.au",
        )
        for n in ["Ada", "Ben"]
    ]
    mia = Student.objects.create(
        tenant_id=tenant_id, first_name="Mia", last_name="Tran", year_level=8,
        enrolment_status="enrolled",
    )
    Guardian.objects.create(
        tenant_id=tenant_id, first_name="Hoa", last_name="Tran", email="hoa@example.com"
    ).students.add(mia)

    ken = Student.objects.create(
        tenant_id=tenant_id, first_name="Ken", last_name="Ito", year_level=8,
        enrolment_status="enrolled",
    )
    Guardian.objects.create(
        tenant_id=tenant_id, first_name="Yui", last_name="Ito", email="yui@example.com"
    ).students.add(ken)
    return teachers, mia, ken


@pytest.fixture
def round_open(tenant_id):
    return InterviewRound.objects.create(
        tenant_id=tenant_id, name="Semester 1",
        bookings_open_at=NOW - timedelta(days=1),
        bookings_close_at=NOW + timedelta(days=7),
        is_published=True, max_bookings_per_student=3,
    )


def _slot(tenant_id, round_obj, teacher, minutes_from_now=60):
    return InterviewSlot.objects.create(
        tenant_id=tenant_id, round=round_obj, teacher=teacher,
        starts_at=NOW + timedelta(minutes=minutes_from_now), duration_minutes=10,
    )


# ── laying out an evening ────────────────────────────────────────────────────
@pytest.mark.django_db
def test_slots_are_generated_across_an_evening(office, tenant_id, round_open, school):
    """Teachers set up "5pm to 8pm, ten minutes each", not eighteen times."""
    teachers, _mia, _ken = school
    start = NOW + timedelta(days=1)
    resp = office.post(f"/api/v1/meetings/interview-rounds/{round_open.id}/generate-slots/", {
        "teacher": str(teachers[0].id),
        "start": start.isoformat(),
        "end": (start + timedelta(hours=1)).isoformat(),
        "duration_minutes": 10,
    }, format="json")

    assert resp.status_code == 201, resp.data
    assert resp.data["created"] == 6


@pytest.mark.django_db
def test_breaks_are_inserted_so_the_evening_does_not_run_late(tenant_id, round_open, school):
    teachers, _mia, _ken = school
    start = NOW + timedelta(days=1)
    slots = interviews.generate_slots(
        round_open, teacher=teachers[0], start=start, end=start + timedelta(hours=1),
        duration_minutes=10, break_after=2, break_minutes=10,
    )
    times = list(slots.order_by("starts_at").values_list("starts_at", flat=True))
    # Two slots, then a ten-minute gap before the third.
    assert (times[2] - times[1]).total_seconds() == 20 * 60


@pytest.mark.django_db
def test_regenerating_tops_up_rather_than_failing(tenant_id, round_open, school):
    teachers, _mia, _ken = school
    start = NOW + timedelta(days=1)
    interviews.generate_slots(
        round_open, teacher=teachers[0], start=start, end=start + timedelta(minutes=30)
    )
    slots = interviews.generate_slots(
        round_open, teacher=teachers[0], start=start, end=start + timedelta(hours=1)
    )
    assert slots.count() == 6


@pytest.mark.django_db
def test_an_end_before_the_start_is_refused(tenant_id, round_open, school):
    teachers, _mia, _ken = school
    start = NOW + timedelta(days=1)
    with pytest.raises(interviews.InterviewError):
        interviews.generate_slots(
            round_open, teacher=teachers[0], start=start, end=start - timedelta(hours=1)
        )


# ── booking ──────────────────────────────────────────────────────────────────
@pytest.mark.django_db
def test_a_parent_books_a_slot(parent, tenant_id, round_open, school):
    teachers, mia, _ken = school
    slot = _slot(tenant_id, round_open, teachers[0])

    resp = parent.post(f"/api/v1/meetings/interview-slots/{slot.id}/book/", {
        "student": str(mia.id),
    }, format="json")

    assert resp.status_code == 201, resp.data
    assert resp.data["status"] == "booked"
    assert resp.data["booked_by_email"] == "hoa@example.com"


@pytest.mark.django_db
def test_a_slot_holds_only_one_booking(parent, other_parent, tenant_id, round_open, school):
    """Two parents pressing "book" at once is the normal case, not an edge case."""
    teachers, mia, ken = school
    slot = _slot(tenant_id, round_open, teachers[0])

    first = parent.post(f"/api/v1/meetings/interview-slots/{slot.id}/book/",
                        {"student": str(mia.id)}, format="json")
    second = other_parent.post(f"/api/v1/meetings/interview-slots/{slot.id}/book/",
                               {"student": str(ken.id)}, format="json")

    assert first.status_code == 201
    assert second.status_code == 409
    assert InterviewBooking.objects.filter(slot=slot, status="booked").count() == 1


@pytest.mark.django_db
def test_a_parent_cannot_book_for_another_familys_child(parent, tenant_id, round_open, school):
    teachers, _mia, ken = school
    slot = _slot(tenant_id, round_open, teachers[0])

    resp = parent.post(f"/api/v1/meetings/interview-slots/{slot.id}/book/",
                       {"student": str(ken.id)}, format="json")
    assert resp.status_code == 403


@pytest.mark.django_db
def test_two_appointments_with_the_same_teacher_are_refused(
    parent, tenant_id, round_open, school
):
    teachers, mia, _ken = school
    first = _slot(tenant_id, round_open, teachers[0], minutes_from_now=60)
    second = _slot(tenant_id, round_open, teachers[0], minutes_from_now=90)

    parent.post(f"/api/v1/meetings/interview-slots/{first.id}/book/",
                {"student": str(mia.id)}, format="json")
    resp = parent.post(f"/api/v1/meetings/interview-slots/{second.id}/book/",
                       {"student": str(mia.id)}, format="json")

    assert resp.status_code == 409
    assert "already have an appointment with this teacher" in resp.data["detail"]


@pytest.mark.django_db
def test_two_appointments_at_the_same_moment_are_refused(
    parent, tenant_id, round_open, school
):
    """A family cannot attend two interviews at once."""
    teachers, mia, _ken = school
    a = _slot(tenant_id, round_open, teachers[0], minutes_from_now=60)
    b = _slot(tenant_id, round_open, teachers[1], minutes_from_now=60)

    parent.post(f"/api/v1/meetings/interview-slots/{a.id}/book/",
                {"student": str(mia.id)}, format="json")
    resp = parent.post(f"/api/v1/meetings/interview-slots/{b.id}/book/",
                       {"student": str(mia.id)}, format="json")

    assert resp.status_code == 409
    assert "already have an appointment at" in resp.data["detail"]


@pytest.mark.django_db
def test_the_per_family_cap_is_enforced(parent, tenant_id, round_open, school):
    """
    Stops one organised family taking every slot before others open the page.
    """
    teachers, mia, _ken = school
    extra = [
        Staff.objects.create(
            tenant_id=tenant_id, first_name=f"T{i}", last_name="Extra",
            role="teacher", email=f"t{i}@cyed.edu.au",
        )
        for i in range(4)
    ]
    for index, teacher in enumerate(extra):
        slot = _slot(tenant_id, round_open, teacher, minutes_from_now=60 + index * 15)
        resp = parent.post(f"/api/v1/meetings/interview-slots/{slot.id}/book/",
                           {"student": str(mia.id)}, format="json")
        if index < round_open.max_bookings_per_student:
            assert resp.status_code == 201
        else:
            assert resp.status_code == 409
            assert "which is the limit" in resp.data["detail"]


# ── the booking window ───────────────────────────────────────────────────────
@pytest.mark.django_db
def test_booking_before_the_round_opens_is_refused(parent, tenant_id, school):
    teachers, mia, _ken = school
    later = InterviewRound.objects.create(
        tenant_id=tenant_id, name="Later",
        bookings_open_at=NOW + timedelta(days=2),
        bookings_close_at=NOW + timedelta(days=5),
        is_published=True,
    )
    slot = _slot(tenant_id, later, teachers[0])

    resp = parent.post(f"/api/v1/meetings/interview-slots/{slot.id}/book/",
                       {"student": str(mia.id)}, format="json")
    assert resp.status_code == 409
    assert "Bookings open at" in resp.data["detail"]


@pytest.mark.django_db
def test_booking_after_the_round_closes_is_refused(parent, tenant_id, school):
    teachers, mia, _ken = school
    past = InterviewRound.objects.create(
        tenant_id=tenant_id, name="Last term",
        bookings_open_at=NOW - timedelta(days=30),
        bookings_close_at=NOW - timedelta(days=2),
        is_published=True,
    )
    slot = _slot(tenant_id, past, teachers[0])

    resp = parent.post(f"/api/v1/meetings/interview-slots/{slot.id}/book/",
                       {"student": str(mia.id)}, format="json")
    assert resp.status_code == 409
    assert "have closed" in resp.data["detail"]


@pytest.mark.django_db
def test_an_unpublished_round_is_invisible_to_families(parent, tenant_id, school):
    """A draft round's slots may still be deleted; booking against them lies."""
    InterviewRound.objects.create(
        tenant_id=tenant_id, name="Draft",
        bookings_open_at=NOW - timedelta(days=1),
        bookings_close_at=NOW + timedelta(days=7),
        is_published=False,
    )
    resp = parent.get("/api/v1/meetings/interview-rounds/")
    rows = resp.data["results"] if isinstance(resp.data, dict) else resp.data
    assert rows == []


@pytest.mark.django_db
def test_a_blocked_slot_is_not_bookable(parent, tenant_id, round_open, school):
    teachers, mia, _ken = school
    slot = _slot(tenant_id, round_open, teachers[0])
    slot.is_available = False
    slot.blocked_reason = "Reserved — school needs to see this family"
    slot.save(update_fields=["is_available", "blocked_reason"])

    resp = parent.post(f"/api/v1/meetings/interview-slots/{slot.id}/book/",
                       {"student": str(mia.id)}, format="json")
    assert resp.status_code == 409
    assert "Reserved" in resp.data["detail"]


# ── cancelling ───────────────────────────────────────────────────────────────
@pytest.mark.django_db
def test_cancelling_frees_the_slot_and_keeps_the_row(
    parent, other_parent, tenant_id, round_open, school
):
    """"Booked then cancelled" reads differently to a teacher than "never booked"."""
    teachers, mia, ken = school
    slot = _slot(tenant_id, round_open, teachers[0])
    booking = parent.post(f"/api/v1/meetings/interview-slots/{slot.id}/book/",
                          {"student": str(mia.id)}, format="json").data["id"]

    parent.post(f"/api/v1/meetings/interview-bookings/{booking}/cancel/", {}, format="json")

    retaken = other_parent.post(f"/api/v1/meetings/interview-slots/{slot.id}/book/",
                                {"student": str(ken.id)}, format="json")
    assert retaken.status_code == 201
    assert InterviewBooking.objects.filter(id=booking, status="cancelled").exists()


@pytest.mark.django_db
def test_cancelling_twice_is_refused(parent, tenant_id, round_open, school):
    teachers, mia, _ken = school
    slot = _slot(tenant_id, round_open, teachers[0])
    booking = parent.post(f"/api/v1/meetings/interview-slots/{slot.id}/book/",
                          {"student": str(mia.id)}, format="json").data["id"]

    parent.post(f"/api/v1/meetings/interview-bookings/{booking}/cancel/", {}, format="json")
    again = parent.post(f"/api/v1/meetings/interview-bookings/{booking}/cancel/", {}, format="json")
    assert again.status_code == 409


# ── the evening as it stands ─────────────────────────────────────────────────
@pytest.mark.django_db
def test_a_family_sees_their_own_evening_in_order(parent, tenant_id, round_open, school):
    teachers, mia, _ken = school
    later = _slot(tenant_id, round_open, teachers[1], minutes_from_now=120)
    earlier = _slot(tenant_id, round_open, teachers[0], minutes_from_now=60)
    for slot in (later, earlier):
        parent.post(f"/api/v1/meetings/interview-slots/{slot.id}/book/",
                    {"student": str(mia.id)}, format="json")

    resp = parent.get(
        f"/api/v1/meetings/interview-rounds/{round_open.id}/my-schedule/?student={mia.id}"
    )
    assert [a["teacher_name"] for a in resp.data["appointments"]] == [
        "Ada Teacher", "Ben Teacher",
    ]


@pytest.mark.django_db
def test_a_teacher_sees_gaps_not_just_bookings(
    client_for, parent, tenant_id, round_open, school
):
    """
    An unbooked slot next to a family the teacher wanted to see is worth a
    phone call, so gaps are shown rather than compressed away.
    """
    teachers, mia, _ken = school
    booked = _slot(tenant_id, round_open, teachers[0], minutes_from_now=60)
    _slot(tenant_id, round_open, teachers[0], minutes_from_now=75)
    parent.post(f"/api/v1/meetings/interview-slots/{booked.id}/book/",
                {"student": str(mia.id)}, format="json")

    teacher_client = client_for(["teacher"], "ada@cyed.edu.au")
    resp = teacher_client.get(f"/api/v1/meetings/interview-rounds/{round_open.id}/my-schedule/")

    assert resp.data["booked"] == 1
    assert resp.data["free"] == 1
    assert len(resp.data["schedule"]) == 2


@pytest.mark.django_db
def test_available_slots_flag_a_familys_own_bookings(parent, tenant_id, round_open, school):
    teachers, mia, _ken = school
    slot = _slot(tenant_id, round_open, teachers[0])
    parent.post(f"/api/v1/meetings/interview-slots/{slot.id}/book/",
                {"student": str(mia.id)}, format="json")

    resp = parent.get(
        f"/api/v1/meetings/interview-rounds/{round_open.id}/slots/?student={mia.id}"
    )
    mine = [r for r in resp.data["results"] if r["booked_by_me"]]
    assert len(mine) == 1


@pytest.mark.django_db
def test_a_booking_cannot_be_created_by_posting_a_row(parent, tenant_id, round_open, school):
    """That path would skip the cap, the clash checks and the window."""
    teachers, mia, _ken = school
    slot = _slot(tenant_id, round_open, teachers[0])
    resp = parent.post("/api/v1/meetings/interview-bookings/", {
        "slot": str(slot.id), "student": str(mia.id),
    }, format="json")
    assert resp.status_code == 405


@pytest.mark.django_db
def test_families_do_not_see_other_families_bookings(
    parent, other_parent, tenant_id, round_open, school
):
    teachers, mia, _ken = school
    slot = _slot(tenant_id, round_open, teachers[0])
    parent.post(f"/api/v1/meetings/interview-slots/{slot.id}/book/",
                {"student": str(mia.id)}, format="json")

    resp = other_parent.get("/api/v1/meetings/interview-bookings/")
    rows = resp.data["results"] if isinstance(resp.data, dict) else resp.data
    assert rows == []
