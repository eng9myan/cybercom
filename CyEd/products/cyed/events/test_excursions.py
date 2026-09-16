"""
Excursions.

The question this feature exists to answer is asked at 8:40am on the morning of
a trip: *who is allowed on the bus*. Everything below defends that answer being
trustworthy — consent evidenced by a signed document, payment read from the
ledger, and a waiver recorded as a decision rather than looking like neglect.
"""

import uuid
from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from products.cyed.docsign.models import SignableDocument
from products.cyed.events import excursions
from products.cyed.events.models import Event, EventParticipation
from products.cyed.fees.models import Invoice, Payment
from products.cyed.health.models import ActionPlan
from products.cyed.sis.models import ClassSection, Enrolment, Guardian, Student

TOMORROW = timezone.now() + timedelta(days=14)


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
def klass(tenant_id):
    section = ClassSection.objects.create(tenant_id=tenant_id, name="8A", year_level=8)
    students = []
    for i, name in enumerate(["Mia", "Ken", "Ana"]):
        s = Student.objects.create(
            tenant_id=tenant_id, first_name=name, last_name=f"S{i}",
            year_level=8, enrolment_status="enrolled",
        )
        Enrolment.objects.create(
            tenant_id=tenant_id, student=s, class_section=section, status="active"
        )
        students.append(s)
    Guardian.objects.create(
        tenant_id=tenant_id, first_name="Hoa", last_name="Tran", email="hoa@example.com"
    ).students.add(students[0])
    return section, students


@pytest.fixture
def excursion(tenant_id):
    return Event.objects.create(
        tenant_id=tenant_id, name="Zoo excursion", event_type="excursion",
        start_at=TOMORROW, departs_at=TOMORROW, returns_at=TOMORROW + timedelta(hours=6),
        location="Melbourne Zoo", requires_consent=True, charge_students=True,
        cost=Decimal("35.00"),
        permission_deadline=(timezone.localdate() + timedelta(days=7)),
        transport_details="Coach from the front gate.",
    )


# ── one action raises both jobs ──────────────────────────────────────────────
@pytest.mark.django_db
def test_inviting_raises_the_permission_and_the_charge_together(
    office, tenant_id, excursion, klass
):
    """A form and an invoice arriving days apart is two jobs for one family."""
    section, students = klass
    resp = office.post(f"/api/v1/events/events/{excursion.id}/invite/", {
        "class_section": str(section.id),
    }, format="json")

    assert resp.status_code == 201, resp.data
    assert resp.data["invited"] == 3
    assert SignableDocument.objects.filter(
        tenant_id=tenant_id, doc_type="permission_slip"
    ).count() == 3
    assert Invoice.objects.filter(tenant_id=tenant_id, amount=Decimal("35.00")).count() == 3


@pytest.mark.django_db
def test_inviting_twice_tops_up_rather_than_duplicating(office, tenant_id, excursion, klass):
    """A late enrolment must not re-invoice everyone already going."""
    section, _students = klass
    office.post(f"/api/v1/events/events/{excursion.id}/invite/",
                {"class_section": str(section.id)}, format="json")
    again = office.post(f"/api/v1/events/events/{excursion.id}/invite/",
                        {"class_section": str(section.id)}, format="json")

    assert again.data["invited"] == 0
    assert again.data["already_invited"] == 3
    assert Invoice.objects.filter(tenant_id=tenant_id).count() == 3


@pytest.mark.django_db
def test_a_free_excursion_raises_no_invoice(office, tenant_id, klass):
    section, _students = klass
    free = Event.objects.create(
        tenant_id=tenant_id, name="Local walk", event_type="excursion",
        start_at=TOMORROW, requires_consent=True, charge_students=False,
    )
    office.post(f"/api/v1/events/events/{free.id}/invite/",
                {"class_section": str(section.id)}, format="json")
    assert Invoice.objects.filter(tenant_id=tenant_id).count() == 0


@pytest.mark.django_db
def test_charging_without_a_cost_is_refused(office, tenant_id):
    """Every child gets a nil invoice that then has to be chased and cancelled."""
    resp = office.post("/api/v1/events/events/", {
        "name": "Broken", "event_type": "excursion",
        "charge_students": True, "cost": "0",
    }, format="json")
    assert resp.status_code == 400
    assert "nil invoice" in str(resp.data)


@pytest.mark.django_db
def test_the_party_cannot_exceed_its_cap(office, tenant_id, klass):
    section, _students = klass
    small = Event.objects.create(
        tenant_id=tenant_id, name="Minibus trip", event_type="excursion",
        start_at=TOMORROW, requires_consent=True, max_participants=2,
    )
    resp = office.post(f"/api/v1/events/events/{small.id}/invite/",
                       {"class_section": str(section.id)}, format="json")
    assert resp.status_code == 409
    assert "place(s) left" in resp.data["detail"]


# ── who is allowed on the bus ────────────────────────────────────────────────
@pytest.mark.django_db
def test_confirming_alone_does_not_clear_a_child(office, parent, tenant_id, excursion, klass):
    """
    Saying yes is not the same as a signed permission and a settled fee. Telling
    the parent what is still outstanding stops them believing they are done.
    """
    section, students = klass
    office.post(f"/api/v1/events/events/{excursion.id}/invite/",
                {"class_section": str(section.id)}, format="json")
    participation = EventParticipation.objects.get(event=excursion, student=students[0])

    resp = parent.post(f"/api/v1/events/participations/{participation.id}/confirm/", {},
                       format="json")
    assert resp.status_code == 200
    assert resp.data["cleared"] is False
    assert set(resp.data["still_needed"]) == {"permission not signed", "fee unpaid"}


@pytest.mark.django_db
def test_a_child_is_cleared_once_signed_and_paid(office, tenant_id, excursion, klass):
    section, students = klass
    office.post(f"/api/v1/events/events/{excursion.id}/invite/",
                {"class_section": str(section.id)}, format="json")
    participation = EventParticipation.objects.get(event=excursion, student=students[0])

    excursions.confirm(participation)
    participation.consent_document.status = "completed"
    participation.consent_document.save(update_fields=["status"])
    Payment.objects.create(
        tenant_id=tenant_id, invoice=participation.invoice, amount=Decimal("35.00")
    )

    participation.refresh_from_db()
    assert participation.is_cleared() is True


@pytest.mark.django_db
def test_readiness_names_exactly_what_is_missing(office, tenant_id, excursion, klass):
    """"Not ready" alone sends an office worker back through three systems."""
    section, students = klass
    office.post(f"/api/v1/events/events/{excursion.id}/invite/",
                {"class_section": str(section.id)}, format="json")

    # One confirmed and signed but unpaid.
    p = EventParticipation.objects.get(event=excursion, student=students[0])
    excursions.confirm(p)
    p.consent_document.status = "completed"
    p.consent_document.save(update_fields=["status"])

    resp = office.get(f"/api/v1/events/events/{excursion.id}/readiness/")
    rows = {r["name"]: r for r in resp.data["results"]}
    assert rows["Mia S0"]["missing"] == ["fee unpaid"]
    assert "not confirmed" in rows["Ken S1"]["missing"]
    assert resp.data["cleared"] == 0
    assert resp.data["not_ready"] == 3


@pytest.mark.django_db
def test_cleared_students_sort_last_so_the_chase_list_is_on_top(
    office, tenant_id, excursion, klass
):
    section, students = klass
    office.post(f"/api/v1/events/events/{excursion.id}/invite/",
                {"class_section": str(section.id)}, format="json")
    p = EventParticipation.objects.get(event=excursion, student=students[0])
    excursions.confirm(p)
    p.consent_document.status = "completed"
    p.consent_document.save(update_fields=["status"])
    excursions.waive_fee(p, reason="Hardship")

    resp = office.get(f"/api/v1/events/events/{excursion.id}/readiness/")
    assert resp.data["results"][-1]["cleared"] is True


# ── hardship ─────────────────────────────────────────────────────────────────
@pytest.mark.django_db
def test_a_waived_fee_clears_the_child_and_cancels_the_invoice(
    office, tenant_id, excursion, klass
):
    """
    A child whose family cannot pay still goes, and the ledger shows a charge
    raised then written off rather than one that never existed.
    """
    section, students = klass
    office.post(f"/api/v1/events/events/{excursion.id}/invite/",
                {"class_section": str(section.id)}, format="json")
    participation = EventParticipation.objects.get(event=excursion, student=students[0])

    resp = office.post(f"/api/v1/events/participations/{participation.id}/waive-fee/", {
        "reason": "Family in financial hardship — approved by principal",
    }, format="json")

    assert resp.status_code == 200
    participation.refresh_from_db()
    assert participation.is_paid() is True
    assert participation.invoice.status == "cancelled"


@pytest.mark.django_db
def test_waiving_needs_a_reason(office, tenant_id, excursion, klass):
    section, students = klass
    office.post(f"/api/v1/events/events/{excursion.id}/invite/",
                {"class_section": str(section.id)}, format="json")
    participation = EventParticipation.objects.get(event=excursion, student=students[0])

    resp = office.post(f"/api/v1/events/participations/{participation.id}/waive-fee/", {},
                       format="json")
    assert resp.status_code == 400


@pytest.mark.django_db
def test_a_waiver_is_visible_as_a_decision(office, tenant_id, excursion, klass):
    """The readiness list must tell a school decision from an unchased family."""
    section, students = klass
    office.post(f"/api/v1/events/events/{excursion.id}/invite/",
                {"class_section": str(section.id)}, format="json")
    participation = EventParticipation.objects.get(event=excursion, student=students[0])
    excursions.waive_fee(participation, reason="Hardship")

    resp = office.get(f"/api/v1/events/events/{excursion.id}/readiness/")
    row = next(r for r in resp.data["results"] if r["name"] == "Mia S0")
    assert row["fee_waived"] is True
    assert "fee unpaid" not in row["missing"]


# ── the roll that travels ────────────────────────────────────────────────────
@pytest.mark.django_db
def test_the_roll_carries_medical_plans_in_full(office, tenant_id, excursion, klass):
    """A teacher in a car park needs the steps, not a link to them."""
    section, students = klass
    ActionPlan.objects.create(
        tenant_id=tenant_id, student=students[0], plan_type="anaphylaxis",
        severity="critical", triggers="Peanuts",
        emergency_steps="1. Lay flat. 2. EpiPen. 3. Call 000.",
        medication="EpiPen Jr", medication_location="Teacher's bag",
    )
    office.post(f"/api/v1/events/events/{excursion.id}/invite/",
                {"class_section": str(section.id)}, format="json")
    for student in students:
        p = EventParticipation.objects.get(event=excursion, student=student)
        excursions.confirm(p)
        p.consent_document.status = "completed"
        p.consent_document.save(update_fields=["status"])
        excursions.waive_fee(p, reason="School funded")

    resp = office.get(f"/api/v1/events/events/{excursion.id}/roll/")
    assert resp.data["count"] == 3
    assert resp.data["with_medical_plans"] == 1
    # Medical students first — read before the bus leaves, not at the zoo.
    assert resp.data["students"][0]["name"] == "Mia S0"
    assert "EpiPen" in resp.data["students"][0]["medical"]["medication"]


@pytest.mark.django_db
def test_the_roll_only_lists_cleared_students(office, tenant_id, excursion, klass):
    """A child who is not cleared is not on the bus, so not on the roll."""
    section, _students = klass
    office.post(f"/api/v1/events/events/{excursion.id}/invite/",
                {"class_section": str(section.id)}, format="json")
    resp = office.get(f"/api/v1/events/events/{excursion.id}/roll/")
    assert resp.data["count"] == 0


# ── chasing ──────────────────────────────────────────────────────────────────
@pytest.mark.django_db
def test_families_are_not_chased_before_the_deadline(office, tenant_id, excursion, klass):
    """Chasing a fortnight early teaches parents to ignore the school."""
    section, _students = klass
    office.post(f"/api/v1/events/events/{excursion.id}/invite/",
                {"class_section": str(section.id)}, format="json")

    resp = office.get(f"/api/v1/events/events/{excursion.id}/chase-list/")
    assert resp.data["due"] is False
    assert resp.data["results"] == []


@pytest.mark.django_db
def test_past_the_deadline_the_chase_list_names_them(office, tenant_id, excursion, klass):
    section, _students = klass
    office.post(f"/api/v1/events/events/{excursion.id}/invite/",
                {"class_section": str(section.id)}, format="json")
    excursion.permission_deadline = timezone.localdate() - timedelta(days=1)
    excursion.save(update_fields=["permission_deadline"])

    resp = office.get(f"/api/v1/events/events/{excursion.id}/chase-list/")
    assert resp.data["due"] is True
    assert resp.data["count"] == 3


# ── access ───────────────────────────────────────────────────────────────────
@pytest.mark.django_db
def test_a_parent_cannot_confirm_another_familys_child(
    office, parent, tenant_id, excursion, klass
):
    section, students = klass
    office.post(f"/api/v1/events/events/{excursion.id}/invite/",
                {"class_section": str(section.id)}, format="json")
    other = EventParticipation.objects.get(event=excursion, student=students[1])

    resp = parent.post(f"/api/v1/events/participations/{other.id}/confirm/", {}, format="json")
    assert resp.status_code in (403, 404)


@pytest.mark.django_db
def test_a_parent_cannot_waive_their_own_fee(office, parent, tenant_id, excursion, klass):
    section, students = klass
    office.post(f"/api/v1/events/events/{excursion.id}/invite/",
                {"class_section": str(section.id)}, format="json")
    participation = EventParticipation.objects.get(event=excursion, student=students[0])

    resp = parent.post(f"/api/v1/events/participations/{participation.id}/waive-fee/", {
        "reason": "I would rather not pay",
    }, format="json")
    assert resp.status_code == 403


@pytest.mark.django_db
def test_consent_cannot_be_patched_true(office, parent, tenant_id, excursion, klass):
    """That would clear a child onto a bus without a signed permission."""
    section, students = klass
    office.post(f"/api/v1/events/events/{excursion.id}/invite/",
                {"class_section": str(section.id)}, format="json")
    participation = EventParticipation.objects.get(event=excursion, student=students[0])
    excursions.confirm(participation)

    parent.patch(f"/api/v1/events/participations/{participation.id}/",
                 {"consent_given": True}, format="json")
    participation.refresh_from_db()
    assert participation.is_consented() is False
