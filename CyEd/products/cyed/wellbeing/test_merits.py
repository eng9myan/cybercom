"""
Merit and demerit points.

Points hang off the behaviour record that already existed, so the tally and the
incident log can never disagree about what a child was given and why. Totals
are always computed — a stored running total drifts, and a drifted merit tally
is one a fifteen-year-old will notice and dispute.
"""

import uuid
from datetime import date

import pytest
from rest_framework.test import APIClient

from products.cyed.sis.models import Student
from products.cyed.wellbeing.models import BehaviourIncident


@pytest.fixture
def client_for(mint_token, mock_jwks, tenant_id):
    def _make(roles, email="teacher@cyed.edu.au"):
        c = APIClient()
        c.credentials(HTTP_AUTHORIZATION=f"Bearer {mint_token({
            'sub': str(uuid.uuid4()), 'email': email, 'tenant_id': str(tenant_id),
            'realm_access': {'roles': roles},
        })}")
        return c
    return _make


@pytest.fixture
def teacher(client_for):
    return client_for(["teacher"])


@pytest.fixture
def students(tenant_id):
    return [
        Student.objects.create(
            tenant_id=tenant_id, first_name=n, last_name=f"S{i}",
            year_level=8, enrolment_status="enrolled",
        )
        for i, n in enumerate(["Ana", "Ben", "Cara"])
    ]


def _incident(client, student, **extra):
    body = {
        "student": str(student.id), "date": date(2026, 8, 11).isoformat(),
        "category": "positive", "description": "Helped a peer",
    }
    body.update(extra)
    return client.post("/api/v1/wellbeing/behaviour-incidents/", body, format="json")


# ── default points ───────────────────────────────────────────────────────────
@pytest.mark.django_db
def test_categories_carry_default_points(teacher, students):
    assert _incident(teacher, students[0], category="positive").data["points"] == 1
    assert _incident(teacher, students[1], category="minor").data["points"] == -1
    assert _incident(teacher, students[2], category="major").data["points"] == -3


@pytest.mark.django_db
def test_an_explicit_weight_overrides_the_default(teacher, students):
    """A school can weight one incident more heavily without a new category."""
    resp = _incident(teacher, students[0], category="positive", points=5)
    assert resp.data["points"] == 5


@pytest.mark.django_db
def test_a_hand_adjusted_value_survives_an_edit(teacher, students):
    created = _incident(teacher, students[0], category="positive", points=5)
    teacher.patch(
        f"/api/v1/wellbeing/behaviour-incidents/{created.data['id']}/",
        {"description": "Corrected wording"}, format="json",
    )
    incident = BehaviourIncident.objects.get(id=created.data["id"])
    assert incident.points == 5


@pytest.mark.django_db
def test_the_reporter_is_stamped_from_the_token(teacher, students):
    resp = _incident(teacher, students[0])
    assert resp.data["reported_by"] == "teacher@cyed.edu.au"


# ── tallies ──────────────────────────────────────────────────────────────────
@pytest.mark.django_db
def test_tally_separates_merits_from_demerits(teacher, tenant_id, students):
    _incident(teacher, students[0], category="positive", points=4)
    _incident(teacher, students[0], category="minor")      # −1
    _incident(teacher, students[0], category="major")      # −3

    resp = teacher.get(f"/api/v1/wellbeing/behaviour-incidents/tally/?student={students[0].id}")
    assert resp.status_code == 200
    assert resp.data["merits"] == 4
    # Reported as a positive magnitude — "4 demerits" reads better than "−4".
    assert resp.data["demerits"] == 4
    assert resp.data["net"] == 0
    assert resp.data["incidents"] == 3


@pytest.mark.django_db
def test_a_student_with_no_incidents_tallies_to_zero(teacher, students):
    resp = teacher.get(f"/api/v1/wellbeing/behaviour-incidents/tally/?student={students[2].id}")
    assert resp.data["net"] == 0
    assert resp.data["incidents"] == 0


@pytest.mark.django_db
def test_deleting_an_incident_moves_the_tally(teacher, students):
    """The tally is derived, so it cannot drift away from the incident log."""
    created = _incident(teacher, students[0], category="positive", points=3)
    before = teacher.get(
        f"/api/v1/wellbeing/behaviour-incidents/tally/?student={students[0].id}"
    ).data["net"]
    assert before == 3

    teacher.delete(f"/api/v1/wellbeing/behaviour-incidents/{created.data['id']}/")
    after = teacher.get(
        f"/api/v1/wellbeing/behaviour-incidents/tally/?student={students[0].id}"
    ).data["net"]
    assert after == 0


@pytest.mark.django_db
def test_tally_can_be_windowed_to_a_term(teacher, tenant_id, students):
    BehaviourIncident.objects.create(
        tenant_id=tenant_id, student=students[0], date=date(2026, 2, 1),
        category="positive", points=10,
    )
    BehaviourIncident.objects.create(
        tenant_id=tenant_id, student=students[0], date=date(2026, 8, 1),
        category="positive", points=2,
    )
    resp = teacher.get(
        f"/api/v1/wellbeing/behaviour-incidents/tally/?student={students[0].id}"
        f"&date_from=2026-07-01"
    )
    assert resp.data["net"] == 2


# ── bulk award ───────────────────────────────────────────────────────────────
@pytest.mark.django_db
def test_a_group_can_be_recognised_in_one_request(teacher, tenant_id, students):
    """A teacher awarding thirty merits one at a time will not do it."""
    resp = teacher.post("/api/v1/wellbeing/behaviour-incidents/award/", {
        "students": [str(s.id) for s in students],
        "category": "positive", "points": 2,
        "description": "Ran the Year 8 assembly", "house": "Kookaburra",
    }, format="json")
    assert resp.status_code == 201, resp.data
    assert resp.data["awarded"] == 3
    assert BehaviourIncident.objects.filter(tenant_id=tenant_id, points=2).count() == 3


@pytest.mark.django_db
def test_bulk_award_applies_default_points_when_none_given(teacher, tenant_id, students):
    """bulk_create skips save(), so the default has to be applied explicitly."""
    teacher.post("/api/v1/wellbeing/behaviour-incidents/award/", {
        "students": [str(s.id) for s in students], "category": "positive",
    }, format="json")
    assert all(
        i.points == 1 for i in BehaviourIncident.objects.filter(tenant_id=tenant_id)
    )


@pytest.mark.django_db
def test_awarding_to_a_student_outside_the_school_is_refused(teacher, students):
    resp = teacher.post("/api/v1/wellbeing/behaviour-incidents/award/", {
        "students": [str(students[0].id), str(uuid.uuid4())], "category": "positive",
    }, format="json")
    assert resp.status_code == 400


@pytest.mark.django_db
def test_an_unknown_category_is_refused(teacher, students):
    resp = teacher.post("/api/v1/wellbeing/behaviour-incidents/award/", {
        "students": [str(students[0].id)], "category": "excellent",
    }, format="json")
    assert resp.status_code == 400


# ── scoreboards ──────────────────────────────────────────────────────────────
@pytest.mark.django_db
def test_leaderboard_ranks_by_net_then_fewest_incidents(teacher, tenant_id, students):
    """
    Ties break on fewest incidents — otherwise the order is arbitrary and
    changes between requests, which students notice.
    """
    BehaviourIncident.objects.create(
        tenant_id=tenant_id, student=students[0], date=date(2026, 8, 1),
        category="positive", points=6,
    )
    for _ in range(3):
        BehaviourIncident.objects.create(
            tenant_id=tenant_id, student=students[1], date=date(2026, 8, 1),
            category="positive", points=2,
        )
    resp = teacher.get("/api/v1/wellbeing/behaviour-incidents/leaderboard/")
    rows = resp.data["results"]
    assert rows[0]["student"] == str(students[0].id)   # same 6 points, fewer incidents
    assert rows[1]["student"] == str(students[1].id)


@pytest.mark.django_db
def test_house_standings_group_points(teacher, tenant_id, students):
    for student, house, points in [
        (students[0], "Kookaburra", 5), (students[1], "Kookaburra", 3), (students[2], "Wombat", 6)
    ]:
        BehaviourIncident.objects.create(
            tenant_id=tenant_id, student=student, date=date(2026, 8, 1),
            category="positive", points=points, house=house,
        )
    resp = teacher.get("/api/v1/wellbeing/behaviour-incidents/houses/")
    rows = {r["house"]: r for r in resp.data["results"]}
    assert rows["Kookaburra"]["net"] == 8
    assert rows["Wombat"]["net"] == 6
    assert resp.data["results"][0]["house"] == "Kookaburra"   # ordered by net


@pytest.mark.django_db
def test_incidents_with_no_house_are_shown_not_dropped(teacher, tenant_id, students):
    """A missing house is a data-entry gap to see, not points that vanish."""
    BehaviourIncident.objects.create(
        tenant_id=tenant_id, student=students[0], date=date(2026, 8, 1),
        category="positive", points=4,
    )
    resp = teacher.get("/api/v1/wellbeing/behaviour-incidents/houses/")
    assert resp.data["results"][0]["house"] == "Unassigned"
    assert resp.data["results"][0]["net"] == 4
