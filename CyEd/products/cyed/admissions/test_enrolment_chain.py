"""
Admissions join-up: catchment, offer response, and the post-enrolment chain.

The audit's finding was that `enrol` created a bare Student and stopped, so
everything an offer implied — household, fees, class, consents — was manual
re-keying. These tests are mostly about the chain producing a student who is
actually ready for their first day, and about the report naming what it could
not do.
"""

import uuid
from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from products.cyed.admissions import enrolment as service
from products.cyed.admissions.models import (
    Application,
    ApplicationDocument,
    CatchmentZone,
    Offer,
)
from products.cyed.billing.models import FeePlan, SiblingDiscountRule, StudentBill
from products.cyed.fees.models import FeeSchedule
from products.cyed.health.models import ImmunisationRecord
from products.cyed.org.models import Campus
from products.cyed.sis.models import ClassSection, Enrolment, Family, Guardian, Student


@pytest.fixture
def registrar(mint_token, mock_jwks, tenant_id):
    token = mint_token({
        "sub": str(uuid.uuid4()), "email": "registrar@cyed.edu.au",
        "tenant_id": str(tenant_id), "realm_access": {"roles": ["tenant_admin"]},
    })
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


@pytest.fixture
def application(tenant_id):
    return Application.objects.create(
        tenant_id=tenant_id,
        applicant_first_name="Mia", applicant_last_name="Tran",
        date_of_birth=date(2015, 4, 2), year_level_applying=3,
        guardian_name="Hoa Tran", guardian_email="hoa@example.com",
        guardian_phone="0400111222",
        residential_address="12 Swan St", residential_suburb="Richmond",
        residential_postcode="3121",
        status="accepted",
    )


@pytest.fixture
def fee_setup(tenant_id):
    plan = FeePlan.objects.create(
        tenant_id=tenant_id, name="Termly", schedule_type="termly", installments_count=3
    )
    FeeSchedule.objects.create(
        tenant_id=tenant_id, name="Year 3 Tuition", amount=Decimal("3000.00"),
        applies_to_year_level=3, is_active=True,
    )
    return plan


def _received(application):
    """Mark the required checklist as sighted."""
    service.ensure_document_checklist(application)
    application.documents.update(is_received=True, received_on=timezone.localdate())


# ── catchment ────────────────────────────────────────────────────────────────
@pytest.mark.django_db
def test_an_address_in_zone_is_matched(tenant_id, application):
    CatchmentZone.objects.create(
        tenant_id=tenant_id, name="Inner East", postcodes=["3121", "3122"],
        suburbs=["Richmond"],
    )
    verdict = service.check_application_catchment(application)
    assert verdict["in_catchment"] is True
    assert verdict["zone_name"] == "Inner East"


@pytest.mark.django_db
def test_an_address_outside_every_zone_is_reported(tenant_id, application):
    CatchmentZone.objects.create(tenant_id=tenant_id, name="Inner East", postcodes=["3000"])
    verdict = service.check_application_catchment(application)
    assert verdict["in_catchment"] is False
    assert "not in any configured zone" in verdict["reason"]


@pytest.mark.django_db
def test_a_priority_zone_wins_when_an_address_falls_in_both(tenant_id, application):
    CatchmentZone.objects.create(tenant_id=tenant_id, name="General", postcodes=["3121"])
    CatchmentZone.objects.create(
        tenant_id=tenant_id, name="Priority", postcodes=["3121"], is_priority=True
    )
    verdict = service.check_application_catchment(application)
    assert verdict["zone_name"] == "Priority"
    assert verdict["is_priority"] is True


@pytest.mark.django_db
def test_no_zones_configured_reads_as_unchecked_not_out_of_zone(tenant_id, application):
    """
    The distinction matters: "we did not check" must never be reported as
    "this family is out of zone".
    """
    verdict = service.check_application_catchment(application)
    assert verdict["checked"] is False
    assert verdict["in_catchment"] is None


@pytest.mark.django_db
def test_a_zone_matching_nothing_is_refused(registrar):
    resp = registrar.post("/api/v1/admissions/catchment-zones/", {
        "name": "Empty", "postcodes": [], "suburbs": [],
    }, format="json")
    assert resp.status_code == 400
    assert "matches nothing" in resp.data["detail"]


# ── offers ───────────────────────────────────────────────────────────────────
@pytest.fixture
def offer(tenant_id, application):
    return Offer.objects.create(
        tenant_id=tenant_id, application=application, offered_year_level=3,
        offer_date=timezone.localdate(),
        expiry_date=timezone.localdate() + timedelta(days=14),
    )


@pytest.mark.django_db
def test_a_family_can_accept_an_offer(registrar, offer, application):
    resp = registrar.post(f"/api/v1/admissions/offers/{offer.id}/accept/", {}, format="json")
    assert resp.status_code == 200, resp.data
    offer.refresh_from_db()
    application.refresh_from_db()
    assert offer.response == "accepted"
    assert offer.responded_on is not None
    assert application.status == "accepted"


@pytest.mark.django_db
def test_a_family_can_decline_with_a_reason(registrar, offer, application):
    resp = registrar.post(
        f"/api/v1/admissions/offers/{offer.id}/decline/",
        {"reason": "Accepted a place elsewhere"}, format="json",
    )
    assert resp.status_code == 200
    offer.refresh_from_db()
    assert offer.response == "declined"
    assert "elsewhere" in offer.decline_reason


@pytest.mark.django_db
def test_an_expired_offer_cannot_be_accepted(registrar, offer):
    offer.expiry_date = timezone.localdate() - timedelta(days=1)
    offer.save(update_fields=["expiry_date"])
    resp = registrar.post(f"/api/v1/admissions/offers/{offer.id}/accept/", {}, format="json")
    assert resp.status_code == 409
    assert "expired" in resp.data["detail"]


@pytest.mark.django_db
def test_accepting_on_the_last_day_still_works(registrar, offer):
    offer.expiry_date = timezone.localdate()
    offer.save(update_fields=["expiry_date"])
    assert registrar.post(
        f"/api/v1/admissions/offers/{offer.id}/accept/", {}, format="json"
    ).status_code == 200


@pytest.mark.django_db
def test_an_answered_offer_cannot_be_answered_twice(registrar, offer):
    registrar.post(f"/api/v1/admissions/offers/{offer.id}/accept/", {}, format="json")
    resp = registrar.post(f"/api/v1/admissions/offers/{offer.id}/decline/", {}, format="json")
    assert resp.status_code == 409


@pytest.mark.django_db
def test_lapsing_frees_places_nobody_answered(registrar, tenant_id, offer, application):
    """
    Without this an unanswered offer holds a place forever and the waitlist
    never moves — a failure that looks like nothing is wrong.
    """
    offer.expiry_date = timezone.localdate() - timedelta(days=1)
    offer.save(update_fields=["expiry_date"])
    resp = registrar.post("/api/v1/admissions/offers/lapse-expired/", {}, format="json")
    assert resp.data["lapsed"] == 1
    offer.refresh_from_db()
    application.refresh_from_db()
    assert offer.response == "declined"
    assert "lapsed" in offer.decline_reason
    assert application.status == "declined"


@pytest.mark.django_db
def test_an_accepted_offer_is_not_lapsed_by_the_daily_job(registrar, offer):
    registrar.post(f"/api/v1/admissions/offers/{offer.id}/accept/", {}, format="json")
    offer.expiry_date = timezone.localdate() - timedelta(days=1)
    offer.save(update_fields=["expiry_date"])
    resp = registrar.post("/api/v1/admissions/offers/lapse-expired/", {}, format="json")
    assert resp.data["lapsed"] == 0


# ── waitlist ─────────────────────────────────────────────────────────────────
@pytest.mark.django_db
def test_waitlist_ranks_in_application_order(registrar, tenant_id):
    for name in ["First", "Second", "Third"]:
        app = Application.objects.create(
            tenant_id=tenant_id, applicant_first_name=name, applicant_last_name="Q",
            year_level_applying=5,
        )
        service.add_to_waitlist(app)
    resp = registrar.get("/api/v1/admissions/applications/waitlist/?year_level=5")
    assert [r["name"] for r in resp.data["results"]] == ["First Q", "Second Q", "Third Q"]
    assert [r["rank"] for r in resp.data["results"]] == [1, 2, 3]


# ── document checklist ───────────────────────────────────────────────────────
@pytest.mark.django_db
def test_checklist_is_idempotent(application):
    assert len(service.ensure_document_checklist(application)) == 3
    assert len(service.ensure_document_checklist(application)) == 0


@pytest.mark.django_db
def test_receiving_a_document_records_who_sighted_it(registrar, application):
    service.ensure_document_checklist(application)
    doc = application.documents.first()
    resp = registrar.post(f"/api/v1/admissions/documents/{doc.id}/receive/", {}, format="json")
    assert resp.status_code == 200
    assert resp.data["received_by"] == "registrar@cyed.edu.au"
    assert resp.data["is_received"] is True


# ── the enrolment chain ──────────────────────────────────────────────────────
@pytest.mark.django_db
def test_enrol_builds_a_student_ready_for_their_first_day(
    registrar, tenant_id, application, fee_setup
):
    _received(application)
    section = ClassSection.objects.create(
        tenant_id=tenant_id, name="3B", year_level=3, capacity=25
    )

    resp = registrar.post(f"/api/v1/admissions/applications/{application.id}/enrol/", {
        "fee_plan": str(fee_setup.id), "class_section": str(section.id),
    }, format="json")
    assert resp.status_code == 201, resp.data

    student = Student.objects.get(id=resp.data["student_id"])
    assert student.enrolment_status == "enrolled"
    # Guardian attached, household opened, fees raised, class allocated,
    # immunisation record opened — none of which used to happen.
    assert student.guardians.filter(email="hoa@example.com").exists()
    assert student.family is not None
    assert student.family.postcode == "3121"
    assert StudentBill.objects.filter(student=student).exists()
    assert Enrolment.objects.filter(student=student, class_section=section).exists()
    assert ImmunisationRecord.objects.get(student=student).status == "not_provided"

    steps = {c["step"] for c in resp.data["created"]}
    assert steps == {"guardian", "family", "billing", "class_allocation", "immunisation_record"}


@pytest.mark.django_db
def test_a_second_child_joins_the_existing_household_and_gets_the_sibling_discount(
    registrar, tenant_id, application, fee_setup
):
    """
    The pay-off for attaching the household first: the discount fires without
    anyone remembering to apply it.
    """
    SiblingDiscountRule.objects.create(
        tenant_id=tenant_id, name="Second child", ordinal=2, percent=Decimal("10")
    )
    family = Family.objects.create(tenant_id=tenant_id, name="Tran Household")
    guardian = Guardian.objects.create(
        tenant_id=tenant_id, family=family, first_name="Hoa", last_name="Tran",
        email="hoa@example.com",
    )
    elder = Student.objects.create(
        tenant_id=tenant_id, family=family, first_name="Bao", last_name="Tran",
        year_level=6, date_of_birth=date(2012, 1, 1), enrolment_status="enrolled",
    )
    elder.guardians.add(guardian)

    _received(application)
    resp = registrar.post(f"/api/v1/admissions/applications/{application.id}/enrol/", {
        "fee_plan": str(fee_setup.id),
    }, format="json")
    assert resp.status_code == 201, resp.data

    student = Student.objects.get(id=resp.data["student_id"])
    assert student.family_id == family.id
    assert Family.objects.filter(tenant_id=tenant_id).count() == 1  # no duplicate household

    bill = StudentBill.objects.get(student=student)
    # 3000 tuition − 10% second-child discount.
    assert sum(i.amount_due for i in bill.installments.all()) == Decimal("2700.00")


@pytest.mark.django_db
def test_the_report_names_what_it_could_not_do(registrar, application):
    """A silent success destroys the information a registrar needs."""
    _received(application)
    resp = registrar.post(
        f"/api/v1/admissions/applications/{application.id}/enrol/", {}, format="json"
    )
    assert resp.status_code == 201
    skipped = {s["step"]: s["reason"] for s in resp.data["skipped"]}
    assert "billing" in skipped and "No fee plan" in skipped["billing"]
    assert "class_allocation" in skipped


@pytest.mark.django_db
def test_missing_fee_schedule_is_reported_not_crashed(registrar, tenant_id, application):
    plan = FeePlan.objects.create(tenant_id=tenant_id, name="Termly", schedule_type="termly")
    _received(application)
    resp = registrar.post(f"/api/v1/admissions/applications/{application.id}/enrol/", {
        "fee_plan": str(plan.id),
    }, format="json")
    assert resp.status_code == 201
    skipped = {s["step"]: s["reason"] for s in resp.data["skipped"]}
    assert "No active fee schedule" in skipped["billing"]


@pytest.mark.django_db
def test_outstanding_documents_block_enrolment(registrar, application):
    service.ensure_document_checklist(application)
    resp = registrar.post(
        f"/api/v1/admissions/applications/{application.id}/enrol/", {}, format="json"
    )
    assert resp.status_code == 409
    assert "documents are outstanding" in resp.data["detail"]


@pytest.mark.django_db
def test_documents_can_be_deliberately_overridden(registrar, application):
    service.ensure_document_checklist(application)
    resp = registrar.post(f"/api/v1/admissions/applications/{application.id}/enrol/", {
        "require_documents": False,
    }, format="json")
    assert resp.status_code == 201


@pytest.mark.django_db
def test_a_full_class_rolls_the_whole_chain_back(registrar, tenant_id, application, fee_setup):
    """
    Half-enrolling a child into a full room is worse than not starting: the
    transaction must leave nothing behind.
    """
    section = ClassSection.objects.create(
        tenant_id=tenant_id, name="3B", year_level=3, capacity=1
    )
    sitting = Student.objects.create(
        tenant_id=tenant_id, first_name="Already", last_name="Here", year_level=3
    )
    Enrolment.objects.create(
        tenant_id=tenant_id, student=sitting, class_section=section, status="active"
    )

    _received(application)
    before = Student.objects.count()
    resp = registrar.post(f"/api/v1/admissions/applications/{application.id}/enrol/", {
        "fee_plan": str(fee_setup.id), "class_section": str(section.id),
    }, format="json")

    assert resp.status_code == 409
    assert "is full" in resp.data["detail"]
    assert Student.objects.count() == before
    application.refresh_from_db()
    assert application.enrolled_student_id is None
    assert application.status == "accepted"


@pytest.mark.django_db
def test_enrolling_twice_is_refused(registrar, application):
    _received(application)
    first = registrar.post(
        f"/api/v1/admissions/applications/{application.id}/enrol/", {}, format="json"
    )
    assert first.status_code == 201
    second = registrar.post(
        f"/api/v1/admissions/applications/{application.id}/enrol/", {}, format="json"
    )
    assert second.status_code == 409
    assert "already been enrolled" in second.data["detail"]


@pytest.mark.django_db
def test_a_declined_application_cannot_be_enrolled(registrar, application):
    application.status = "declined"
    application.save(update_fields=["status"])
    resp = registrar.post(f"/api/v1/admissions/applications/{application.id}/enrol/", {
        "require_documents": False,
    }, format="json")
    assert resp.status_code == 409


@pytest.mark.django_db
def test_an_unknown_fee_plan_id_is_a_clear_400(registrar, application):
    _received(application)
    resp = registrar.post(f"/api/v1/admissions/applications/{application.id}/enrol/", {
        "fee_plan": str(uuid.uuid4()),
    }, format="json")
    assert resp.status_code == 400
    assert "No FeePlan" in resp.data["detail"]
