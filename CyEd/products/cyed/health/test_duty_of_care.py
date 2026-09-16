"""
Immunisation register and medication administration.

Both are duty-of-care records, so the tests here are mostly about what the
system *refuses*: an exclusion list that quietly omits a child with no record,
or a medication log that accepts a fourth dose of a three-a-day drug, would
each document a failure instead of preventing it.
"""

import uuid
from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from products.cyed.health import services
from products.cyed.health.models import (
    ImmunisationDose,
    ImmunisationRecord,
    MedicationAdministration,
    MedicationAuthority,
)
from products.cyed.hr.models import Staff
from products.cyed.sis.models import Guardian, Student


@pytest.fixture
def client_for(mint_token, mock_jwks, tenant_id):
    def _make(roles, email="nurse@cyed.edu.au"):
        token = mint_token({
            "sub": str(uuid.uuid4()), "email": email, "tenant_id": str(tenant_id),
            "realm_access": {"roles": roles},
        })
        c = APIClient()
        c.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        return c
    return _make


@pytest.fixture
def nurse(client_for):
    return client_for(["pastoral"], email="nurse@cyed.edu.au")


@pytest.fixture
def principal(client_for):
    return client_for(["leadership"], email="principal@cyed.edu.au")


@pytest.fixture
def student(tenant_id):
    return Student.objects.create(
        tenant_id=tenant_id, first_name="Mia", last_name="Tran",
        year_level=3, enrolment_status="enrolled",
    )


@pytest.fixture
def first_aider(tenant_id):
    return Staff.objects.create(
        tenant_id=tenant_id, first_name="Sam", last_name="Okafor",
        role="support", email="sam@cyed.edu.au",
    )


def _immunised(student, diseases, *, status="up_to_date", verified=True):
    record = ImmunisationRecord.objects.create(
        tenant_id=student.tenant_id, student=student, status=status,
        air_statement_on=date(2026, 1, 15),
        verified_on=date(2026, 1, 20) if verified else None,
        verified_by="registrar@cyed.edu.au" if verified else "",
        exemption_reason="Anaphylaxis to vaccine component" if status == "medical_exemption" else "",
    )
    for disease in diseases:
        ImmunisationDose.objects.create(
            tenant_id=student.tenant_id, record=record, disease=disease,
            dose_number=1, given_on=date(2020, 5, 1),
        )
    return record


# ── immunisation register ────────────────────────────────────────────────────
@pytest.mark.django_db
def test_a_verified_up_to_date_record_satisfies_enrolment(student):
    record = _immunised(student, ["measles", "mumps", "rubella"])
    assert record.is_acceptable_at_enrolment() is True


@pytest.mark.django_db
def test_an_unverified_statement_does_not_satisfy_enrolment(student):
    """A status nobody sighted is not evidence."""
    record = _immunised(student, ["measles"], verified=False)
    assert record.is_acceptable_at_enrolment() is False


@pytest.mark.django_db
def test_a_catch_up_schedule_is_acceptable(student):
    """The child is being brought up to date under medical supervision."""
    record = _immunised(student, [], status="catch_up")
    assert record.is_acceptable_at_enrolment() is True


@pytest.mark.django_db
def test_gaps_include_students_with_no_record_at_all(tenant_id, student):
    """
    The case a query over existing rows silently misses: a child nobody has
    asked about looks identical to a compliant one.
    """
    compliant = Student.objects.create(
        tenant_id=tenant_id, first_name="Ok", last_name="Student",
        year_level=4, enrolment_status="enrolled",
    )
    _immunised(compliant, ["measles"])

    rows = services.immunisation_gaps(tenant_id)
    assert [r["name"] for r in rows] == ["Mia Tran"]
    assert rows[0]["status"] == "no_record"
    assert "No immunisation record" in rows[0]["reason"]


@pytest.mark.django_db
def test_withdrawn_students_are_not_chased_for_immunisation(tenant_id):
    Student.objects.create(
        tenant_id=tenant_id, first_name="Left", last_name="School",
        year_level=6, enrolment_status="withdrawn",
    )
    assert services.immunisation_gaps(tenant_id) == []


@pytest.mark.django_db
def test_outbreak_exclusion_lists_the_unprotected(tenant_id, student):
    protected = Student.objects.create(
        tenant_id=tenant_id, first_name="Safe", last_name="Child",
        year_level=3, enrolment_status="enrolled",
    )
    _immunised(protected, ["measles", "mumps"])
    _immunised(student, ["tetanus"])  # immunised, but not against measles

    result = services.outbreak_exclusion_list(tenant_id, "measles")
    assert result["count"] == 1
    assert result["students"][0]["name"] == "Mia Tran"
    assert "No recorded dose" in result["students"][0]["basis"]


@pytest.mark.django_db
def test_a_medical_exemption_is_not_protection_during_an_outbreak(tenant_id, student):
    """
    An exempt child is precisely the one an exclusion directive protects.
    Treating "lawfully enrolled" as "safe" would invert the register's purpose.
    """
    _immunised(student, [], status="medical_exemption")
    result = services.outbreak_exclusion_list(tenant_id, "measles")
    assert result["count"] == 1
    assert result["students"][0]["status"] == "medical_exemption"


@pytest.mark.django_db
def test_exclusion_endpoint_rejects_an_unknown_disease(nurse):
    resp = nurse.get("/api/v1/health/immunisations/outbreak-exclusions/?disease=lumbago")
    assert resp.status_code == 400
    assert "Unknown disease" in resp.data["detail"]


@pytest.mark.django_db
def test_medical_exemption_requires_a_recorded_reason(nurse, student):
    resp = nurse.post("/api/v1/health/immunisations/", {
        "student": str(student.id), "status": "medical_exemption",
    }, format="json")
    assert resp.status_code == 400
    # Field errors are flattened into `detail` by the project's RFC7807 handler.
    assert "exemption_reason" in resp.data["detail"]


@pytest.mark.django_db
def test_verifier_is_stamped_from_the_authenticated_user(nurse, student):
    resp = nurse.post("/api/v1/health/immunisations/", {
        "student": str(student.id), "status": "up_to_date",
        "verified_on": "2026-02-01",
        "verified_by": "someone.else@example.com",  # must be ignored
    }, format="json")
    assert resp.status_code == 201, resp.data
    assert resp.data["verified_by"] == "nurse@cyed.edu.au"


@pytest.mark.django_db
def test_immunisation_data_is_not_readable_by_a_teacher(client_for, student):
    _immunised(student, ["measles"])
    teacher = client_for(["teacher"], email="teacher@cyed.edu.au")
    assert teacher.get("/api/v1/health/immunisations/").status_code == 403


# ── medication: the authority ────────────────────────────────────────────────
@pytest.fixture
def authority(tenant_id, student):
    guardian = Guardian.objects.create(
        tenant_id=tenant_id, first_name="Hoa", last_name="Tran", email="hoa@example.com"
    )
    return MedicationAuthority.objects.create(
        tenant_id=tenant_id, student=student, medication_name="Salbutamol",
        dose="2 puffs", route="inhaled", max_doses_per_day=3,
        min_hours_between_doses=Decimal("4.0"),
        prescriber_name="Dr Patel", authorised_by=guardian,
        start_date=date(2026, 1, 1), end_date=date(2026, 12, 31),
        self_administer_permitted=False, is_active=True,
    )


def _give(client, authority, staff, **body):
    payload = {"administered_by": str(staff.id), "dose_given": "2 puffs"}
    payload.update(body)
    return client.post(
        f"/api/v1/health/medication-authorities/{authority.id}/administer/",
        payload, format="json",
    )


@pytest.mark.django_db
def test_a_dose_is_recorded_with_who_gave_it(nurse, authority, first_aider):
    resp = _give(nurse, authority, first_aider)
    assert resp.status_code == 201, resp.data
    assert resp.data["outcome"] == "given"
    assert resp.data["administered_by_name"] == "Sam Okafor"
    assert resp.data["medication_name"] == "Salbutamol"


@pytest.mark.django_db
def test_a_dose_without_a_named_administering_staff_member_is_refused(nurse, authority):
    """"The office" is not accountable; a named person is."""
    resp = nurse.post(
        f"/api/v1/health/medication-authorities/{authority.id}/administer/",
        {"dose_given": "2 puffs"}, format="json",
    )
    assert resp.status_code == 400
    assert "administered_by" in resp.data["detail"]


@pytest.mark.django_db
def test_the_daily_maximum_is_enforced(nurse, authority, first_aider, tenant_id):
    now = timezone.now()
    for i in range(3):
        MedicationAdministration.objects.create(
            tenant_id=tenant_id, authority=authority, student=authority.student,
            administered_at=now - timedelta(hours=12 - i), administered_on=timezone.localdate(),
            dose_given="2 puffs", outcome="given", administered_by=first_aider,
        )
    resp = _give(nurse, authority, first_aider)
    assert resp.status_code == 409
    assert "3 dose(s) already given today" in resp.data["detail"]


@pytest.mark.django_db
def test_the_minimum_interval_between_doses_is_enforced(nurse, authority, first_aider, tenant_id):
    MedicationAdministration.objects.create(
        tenant_id=tenant_id, authority=authority, student=authority.student,
        administered_at=timezone.now() - timedelta(hours=1), administered_on=timezone.localdate(),
        dose_given="2 puffs", outcome="given", administered_by=first_aider,
    )
    resp = _give(nurse, authority, first_aider)
    assert resp.status_code == 409
    assert "must elapse between doses" in resp.data["detail"]


@pytest.mark.django_db
def test_an_expired_authority_cannot_be_used(nurse, authority, first_aider):
    authority.end_date = timezone.localdate() - timedelta(days=1)
    authority.save(update_fields=["end_date"])
    resp = _give(nurse, authority, first_aider)
    assert resp.status_code == 409
    assert "expired" in resp.data["detail"]


@pytest.mark.django_db
def test_a_withdrawn_authority_cannot_be_used(nurse, authority, first_aider):
    authority.is_active = False
    authority.save(update_fields=["is_active"])
    resp = _give(nurse, authority, first_aider)
    assert resp.status_code == 409
    assert "withdrawn" in resp.data["detail"]


@pytest.mark.django_db
def test_self_administration_needs_the_authority_to_permit_it(nurse, authority, first_aider):
    resp = _give(nurse, authority, first_aider, self_administered=True)
    assert resp.status_code == 409
    assert "does not permit" in resp.data["detail"]


@pytest.mark.django_db
def test_self_administration_is_allowed_when_the_plan_says_so(nurse, authority, first_aider):
    authority.self_administer_permitted = True
    authority.save(update_fields=["self_administer_permitted"])
    resp = _give(nurse, authority, first_aider, self_administered=True)
    assert resp.status_code == 201


# ── refusals and omissions are the point ─────────────────────────────────────
@pytest.mark.django_db
def test_a_refusal_is_always_recordable(nurse, authority, first_aider, tenant_id):
    """
    Logging "not given" is why the record exists. Blocking it would destroy the
    evidence of exactly the event that matters.
    """
    for i in range(3):
        MedicationAdministration.objects.create(
            tenant_id=tenant_id, authority=authority, student=authority.student,
            administered_at=timezone.now() - timedelta(hours=12 - i),
            administered_on=timezone.localdate(), dose_given="2 puffs",
            outcome="given", administered_by=first_aider,
        )
    # Over the daily max, but a refusal still has to go on the record.
    resp = _give(nurse, authority, first_aider, outcome="refused", notes="Spat it out")
    assert resp.status_code == 201
    assert resp.data["outcome"] == "refused"


@pytest.mark.django_db
def test_a_refusal_does_not_consume_the_daily_allowance(nurse, authority, first_aider):
    _give(nurse, authority, first_aider, outcome="refused")
    assert authority.doses_given_on(timezone.localdate()) == 0


# ── overrides ────────────────────────────────────────────────────────────────
@pytest.mark.django_db
def test_leadership_can_override_a_limit_with_a_reason(
    principal, authority, first_aider, tenant_id
):
    MedicationAdministration.objects.create(
        tenant_id=tenant_id, authority=authority, student=authority.student,
        administered_at=timezone.now() - timedelta(minutes=30),
        administered_on=timezone.localdate(), dose_given="2 puffs",
        outcome="given", administered_by=first_aider,
    )
    resp = _give(
        principal, authority, first_aider,
        override_reason="Dr Patel authorised an extra dose by phone",
    )
    assert resp.status_code == 201, resp.data
    record = MedicationAdministration.objects.get(id=resp.data["id"])
    assert record.limit_override_by == "principal@cyed.edu.au"
    assert "Dr Patel" in record.limit_override_reason


@pytest.mark.django_db
def test_a_first_aider_cannot_override_a_limit(nurse, authority, first_aider, tenant_id):
    MedicationAdministration.objects.create(
        tenant_id=tenant_id, authority=authority, student=authority.student,
        administered_at=timezone.now() - timedelta(minutes=30),
        administered_on=timezone.localdate(), dose_given="2 puffs",
        outcome="given", administered_by=first_aider,
    )
    resp = _give(nurse, authority, first_aider, override_reason="seemed fine")
    assert resp.status_code == 403


# ── the log itself ───────────────────────────────────────────────────────────
@pytest.mark.django_db
def test_the_log_cannot_be_written_to_directly(nurse, authority, first_aider):
    """Posting a row would bypass every safety check."""
    resp = nurse.post("/api/v1/health/medication-log/", {
        "authority": str(authority.id), "student": str(authority.student_id),
        "administered_at": timezone.now().isoformat(), "dose_given": "99 puffs",
        "administered_by": str(first_aider.id),
    }, format="json")
    assert resp.status_code == 405


@pytest.mark.django_db
def test_the_log_cannot_be_amended_after_the_fact(nurse, authority, first_aider):
    """A record that can be edited in place is not evidence of what happened."""
    created = _give(nurse, authority, first_aider)
    resp = nurse.patch(
        f"/api/v1/health/medication-log/{created.data['id']}/",
        {"dose_given": "1 puff"}, format="json",
    )
    assert resp.status_code == 405


@pytest.mark.django_db
def test_due_today_shows_what_is_left(nurse, authority, first_aider):
    _give(nurse, authority, first_aider)
    resp = nurse.get("/api/v1/health/medication-authorities/due-today/")
    assert resp.status_code == 200
    row = resp.data["results"][0]
    assert row["medication"] == "Salbutamol"
    assert row["given_today"] == 1
    assert row["remaining_today"] == 2


@pytest.mark.django_db
def test_check_lets_a_ui_warn_before_the_click(nurse, authority, first_aider, tenant_id):
    MedicationAdministration.objects.create(
        tenant_id=tenant_id, authority=authority, student=authority.student,
        administered_at=timezone.now() - timedelta(minutes=10),
        administered_on=timezone.localdate(), dose_given="2 puffs",
        outcome="given", administered_by=first_aider,
    )
    resp = nurse.get(f"/api/v1/health/medication-authorities/{authority.id}/check/")
    assert resp.status_code == 200
    assert resp.data["permitted"] is False
    assert "must elapse" in resp.data["reason"]


@pytest.mark.django_db
def test_an_authority_cannot_end_before_it_begins(nurse, student):
    resp = nurse.post("/api/v1/health/medication-authorities/", {
        "student": str(student.id), "medication_name": "Amoxicillin", "dose": "5 mL",
        "start_date": "2026-05-01", "end_date": "2026-04-01",
    }, format="json")
    assert resp.status_code == 400


@pytest.mark.django_db
def test_a_zero_dose_ceiling_is_refused_as_a_disguised_withdrawal(nurse, student):
    resp = nurse.post("/api/v1/health/medication-authorities/", {
        "student": str(student.id), "medication_name": "Amoxicillin", "dose": "5 mL",
        "max_doses_per_day": 0,
    }, format="json")
    assert resp.status_code == 400
    assert "is_active=false" in str(resp.data)
