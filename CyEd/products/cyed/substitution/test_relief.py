"""
CRT (casual relief teacher) register and booking.

The step after the substitution engine runs out of colleagues. The tests below
are mostly about the ways a class could end up unattended while the board says
it is covered: an unbookable person offered work, a double-booked CRT, or an
unanswered offer counted as cover.
"""

import uuid
from datetime import date, timedelta
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from products.cyed.substitution import relief
from products.cyed.substitution.models import (
    ReliefAvailability,
    ReliefBooking,
    ReliefTeacher,
    SubstitutionPlan,
)

MONDAY = date(2026, 8, 17)


@pytest.fixture
def client_for(mint_token, mock_jwks, tenant_id):
    def _make(roles, email="organiser@cyed.edu.au"):
        c = APIClient()
        c.credentials(HTTP_AUTHORIZATION=f"Bearer {mint_token({
            'sub': str(uuid.uuid4()), 'email': email, 'tenant_id': str(tenant_id),
            'realm_access': {'roles': roles},
        })}")
        return c
    return _make


@pytest.fixture
def organiser(client_for):
    return client_for(["tenant_admin"])


def _crt(tenant_id, first="Jo", last="Relief", *, cleared=True, **extra):
    body = {
        "tenant_id": tenant_id,
        "first_name": first,
        "last_name": last,
        "phone": "0400111222",
        "subjects": "Mathematics, Science",
        "daily_rate": Decimal("450.00"),
        "half_day_rate": Decimal("250.00"),
        "status": "active",
    }
    if cleared:
        body.update({
            "wwcc_number": "WWC123",
            "wwcc_expires_on": MONDAY + timedelta(days=365),
            "registration_number": "VIT456",
            "registration_expires_on": MONDAY + timedelta(days=365),
            "verified_on": MONDAY - timedelta(days=30),
            "verified_by": "registrar@cyed.edu.au",
        })
    body.update(extra)
    return ReliefTeacher.objects.create(**body)


def _free(tenant_id, teacher, day=MONDAY):
    return ReliefAvailability.objects.create(
        tenant_id=tenant_id, relief_teacher=teacher, date=day
    )


# ── clearances ───────────────────────────────────────────────────────────────
@pytest.mark.django_db
def test_a_cleared_crt_may_teach(tenant_id):
    assert _crt(tenant_id).may_teach(MONDAY) is True


@pytest.mark.django_db
def test_a_crt_with_no_clearances_recorded_cannot_teach(tenant_id):
    """An agency's assurance is not a sighted card."""
    teacher = _crt(tenant_id, cleared=False)
    state = teacher.clearance_state(MONDAY)
    assert state["may_teach"] is False
    assert "no WWCC recorded" in state["problems"]


@pytest.mark.django_db
def test_an_expired_wwcc_blocks_booking(tenant_id):
    teacher = _crt(tenant_id, wwcc_expires_on=MONDAY - timedelta(days=1))
    assert "WWCC expired" in teacher.clearance_state(MONDAY)["problems"]


@pytest.mark.django_db
def test_unverified_clearances_block_booking(tenant_id):
    """Numbers typed in without anyone sighting the card prove nothing."""
    teacher = _crt(tenant_id, verified_on=None)
    assert teacher.may_teach(MONDAY) is False


# ── finding someone ──────────────────────────────────────────────────────────
@pytest.mark.django_db
def test_only_crts_who_stated_availability_are_offered(organiser, tenant_id):
    """Ringing people at 7am on the off-chance is what this replaces."""
    free = _crt(tenant_id, "Ada", "Free")
    _crt(tenant_id, "Ben", "Unstated")
    _free(tenant_id, free)

    resp = organiser.get(f"/api/v1/substitution/relief-teachers/available/?date={MONDAY}")
    assert [r["name"] for r in resp.data["results"]] == ["Ada Free"]


@pytest.mark.django_db
def test_unbookable_crts_are_excluded_not_greyed_out(organiser, tenant_id):
    """An organiser under time pressure will ring the first name on the list."""
    lapsed = _crt(tenant_id, "Lapsed", "One", wwcc_expires_on=MONDAY - timedelta(days=5))
    _free(tenant_id, lapsed)

    resp = organiser.get(f"/api/v1/substitution/relief-teachers/available/?date={MONDAY}")
    assert resp.data["count"] == 0


@pytest.mark.django_db
def test_subject_specialists_sort_first(organiser, tenant_id):
    generalist = _crt(tenant_id, "Gen", "Eralist", subjects="English",
                      daily_rate=Decimal("300.00"))
    specialist = _crt(tenant_id, "Spec", "Ialist", subjects="Mathematics",
                      daily_rate=Decimal("500.00"))
    _free(tenant_id, generalist)
    _free(tenant_id, specialist)

    resp = organiser.get(
        f"/api/v1/substitution/relief-teachers/available/?date={MONDAY}&subject=Maths"
    )
    # "Maths" must match "Mathematics" — and beat the cheaper generalist.
    assert resp.data["results"][0]["name"] == "Spec Ialist"
    assert resp.data["results"][0]["subject_match"] is True


@pytest.mark.django_db
def test_someone_already_booked_is_not_offered_again(organiser, tenant_id):
    teacher = _crt(tenant_id)
    _free(tenant_id, teacher)
    relief.offer(teacher, day=MONDAY)

    resp = organiser.get(f"/api/v1/substitution/relief-teachers/available/?date={MONDAY}")
    assert resp.data["count"] == 0


@pytest.mark.django_db
def test_the_chase_list_explains_an_empty_search(organiser, tenant_id):
    _crt(tenant_id, "Lapsed", "One", wwcc_expires_on=MONDAY - timedelta(days=5))
    resp = organiser.get("/api/v1/substitution/relief-teachers/clearance-issues/")
    assert resp.data["count"] == 1
    assert "WWCC expired" in resp.data["results"][0]["problems"]


# ── offering work ────────────────────────────────────────────────────────────
@pytest.mark.django_db
def test_offering_work_creates_an_offer_not_a_confirmation(organiser, tenant_id):
    """A booking is only cover once the CRT has said yes."""
    teacher = _crt(tenant_id)
    _free(tenant_id, teacher)

    resp = organiser.post(f"/api/v1/substitution/relief-teachers/{teacher.id}/offer/", {
        "date": MONDAY.isoformat(), "periods": "P1, P2", "is_full_day": False,
    }, format="json")

    assert resp.status_code == 201, resp.data
    assert resp.data["status"] == "offered"
    # Half-day work is charged at the half-day rate.
    assert Decimal(resp.data["agreed_rate"]) == Decimal("250.00")


@pytest.mark.django_db
def test_the_rate_is_frozen_at_offer_time(organiser, tenant_id):
    """A rate rise next term must not rewrite what was already agreed."""
    teacher = _crt(tenant_id)
    _free(tenant_id, teacher)
    booking = relief.offer(teacher, day=MONDAY)

    teacher.daily_rate = Decimal("999.00")
    teacher.save(update_fields=["daily_rate"])

    booking.refresh_from_db()
    assert booking.agreed_rate == Decimal("450.00")


@pytest.mark.django_db
def test_an_unbookable_crt_cannot_be_offered_work(organiser, tenant_id):
    teacher = _crt(tenant_id, cleared=False)
    resp = organiser.post(f"/api/v1/substitution/relief-teachers/{teacher.id}/offer/", {
        "date": MONDAY.isoformat(),
    }, format="json")
    assert resp.status_code == 409
    assert "cannot be booked" in resp.data["detail"]


@pytest.mark.django_db
def test_a_do_not_book_crt_is_refused_with_the_reason(organiser, tenant_id):
    teacher = _crt(tenant_id, status="do_not_book",
                   do_not_book_reason="Left a Year 8 class unsupervised")
    resp = organiser.post(f"/api/v1/substitution/relief-teachers/{teacher.id}/offer/", {
        "date": MONDAY.isoformat(),
    }, format="json")
    assert resp.status_code == 409
    assert "unsupervised" in resp.data["detail"]


@pytest.mark.django_db
def test_do_not_book_requires_a_reason(organiser, tenant_id):
    resp = organiser.post("/api/v1/substitution/relief-teachers/", {
        "first_name": "No", "last_name": "Reason", "status": "do_not_book",
    }, format="json")
    assert resp.status_code == 400
    assert "Record why" in str(resp.data)


@pytest.mark.django_db
def test_a_crt_cannot_be_double_booked_on_one_day(organiser, tenant_id):
    """A CRT booked twice is a class standing in a corridor."""
    teacher = _crt(tenant_id)
    _free(tenant_id, teacher)
    relief.offer(teacher, day=MONDAY)

    resp = organiser.post(f"/api/v1/substitution/relief-teachers/{teacher.id}/offer/", {
        "date": MONDAY.isoformat(),
    }, format="json")
    assert resp.status_code == 409
    assert "already has a booking" in resp.data["detail"]


@pytest.mark.django_db
def test_a_declined_booking_frees_the_day(organiser, tenant_id):
    teacher = _crt(tenant_id)
    _free(tenant_id, teacher)
    booking = relief.offer(teacher, day=MONDAY)
    organiser.post(f"/api/v1/substitution/relief-bookings/{booking.id}/decline/",
                   {"note": "Already working elsewhere"}, format="json")

    resp = organiser.post(f"/api/v1/substitution/relief-teachers/{teacher.id}/offer/", {
        "date": MONDAY.isoformat(),
    }, format="json")
    assert resp.status_code == 201


# ── responses ────────────────────────────────────────────────────────────────
@pytest.mark.django_db
def test_accepting_confirms_the_booking(organiser, tenant_id):
    teacher = _crt(tenant_id)
    _free(tenant_id, teacher)
    booking = relief.offer(teacher, day=MONDAY)

    resp = organiser.post(
        f"/api/v1/substitution/relief-bookings/{booking.id}/accept/", {}, format="json"
    )
    assert resp.data["status"] == "accepted"
    assert resp.data["responded_at"] is not None


@pytest.mark.django_db
def test_answering_twice_is_refused(organiser, tenant_id):
    teacher = _crt(tenant_id)
    _free(tenant_id, teacher)
    booking = relief.offer(teacher, day=MONDAY)
    organiser.post(f"/api/v1/substitution/relief-bookings/{booking.id}/accept/", {}, format="json")

    again = organiser.post(
        f"/api/v1/substitution/relief-bookings/{booking.id}/decline/", {}, format="json"
    )
    assert again.status_code == 409


@pytest.mark.django_db
def test_a_cancelled_booking_is_kept_not_deleted(organiser, tenant_id):
    """A CRT who turned down other work deserves a record of it."""
    teacher = _crt(tenant_id)
    _free(tenant_id, teacher)
    booking = relief.offer(teacher, day=MONDAY)
    organiser.post(f"/api/v1/substitution/relief-bookings/{booking.id}/accept/", {}, format="json")

    organiser.post(f"/api/v1/substitution/relief-bookings/{booking.id}/cancel/",
                   {"reason": "Teacher returned"}, format="json")
    booking.refresh_from_db()
    assert booking.status == "cancelled"
    assert ReliefBooking.objects.filter(id=booking.id).exists()


@pytest.mark.django_db
def test_a_booking_cannot_be_created_by_posting_a_row(organiser, tenant_id):
    """That path would skip the clearance and double-booking checks."""
    teacher = _crt(tenant_id)
    resp = organiser.post("/api/v1/substitution/relief-bookings/", {
        "relief_teacher": str(teacher.id), "date": MONDAY.isoformat(),
    }, format="json")
    assert resp.status_code == 405


# ── plan coverage and cost ───────────────────────────────────────────────────
@pytest.mark.django_db
def test_only_accepted_bookings_count_as_cover(organiser, tenant_id):
    plan = SubstitutionPlan.objects.create(
        tenant_id=tenant_id, absent_teacher="Sam Ellis", day_of_week="mon", date=MONDAY
    )
    teacher = _crt(tenant_id)
    _free(tenant_id, teacher)
    booking = relief.offer(teacher, day=MONDAY, plan=plan)

    before = organiser.get(f"/api/v1/substitution/plans/{plan.id}/coverage/")
    assert before.data["relief_booked"] == 0

    organiser.post(f"/api/v1/substitution/relief-bookings/{booking.id}/accept/", {}, format="json")
    after = organiser.get(f"/api/v1/substitution/plans/{plan.id}/coverage/")
    assert after.data["relief_booked"] == 1
    assert after.data["relief"][0]["relief_teacher"] == "Jo Relief"


@pytest.mark.django_db
def test_the_cost_report_totals_accepted_work(organiser, tenant_id):
    """The figure a business manager is asked for at every finance meeting."""
    a = _crt(tenant_id, "Ada", "One")
    b = _crt(tenant_id, "Ben", "Two", daily_rate=Decimal("400.00"))
    _free(tenant_id, a)
    _free(tenant_id, b)
    for teacher in (a, b):
        booking = relief.offer(teacher, day=MONDAY)
        relief.respond(booking, accepted=True)

    resp = organiser.get("/api/v1/substitution/relief-bookings/cost-report/")
    assert Decimal(resp.data["total_cost"]) == Decimal("850.00")
    assert resp.data["by_teacher"][0]["name"] == "Ada One"   # highest cost first


@pytest.mark.django_db
def test_declined_work_costs_nothing(organiser, tenant_id):
    teacher = _crt(tenant_id)
    _free(tenant_id, teacher)
    booking = relief.offer(teacher, day=MONDAY)
    relief.respond(booking, accepted=False)

    resp = organiser.get("/api/v1/substitution/relief-bookings/cost-report/")
    assert Decimal(resp.data["total_cost"]) == Decimal("0")


@pytest.mark.django_db
def test_the_register_is_staff_only(client_for, tenant_id):
    _crt(tenant_id)
    parent = client_for(["parent"], "p@example.com")
    assert parent.get("/api/v1/substitution/relief-teachers/").status_code == 403
