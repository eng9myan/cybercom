"""
The end of a student's time at the school.

Enrolment was well covered; leaving was a status change and nothing else. These
tests cover the exit workflow, the Transfer Certificate a receiving school asks
for, and the alumni list that the graduated/withdrawn distinction makes possible.
"""

import uuid
from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from products.cyed.billing.models import BillLineItem, FeePlan, StudentBill
from products.cyed.billing.services import generate_installments, record_payment
from products.cyed.library.models import Book, Loan
from products.cyed.sis.lifecycle import LifecycleError, alumni, exit_student
from products.cyed.sis.models import ClassSection, Enrolment, Family, Student, TransferCertificate


@pytest.fixture
def client_for(mint_token, mock_jwks, tenant_id):
    def _make(roles, email="registrar@cyed.edu.au"):
        c = APIClient()
        c.credentials(HTTP_AUTHORIZATION=f"Bearer {mint_token({
            'sub': str(uuid.uuid4()), 'email': email, 'tenant_id': str(tenant_id),
            'realm_access': {'roles': roles},
        })}")
        return c
    return _make


@pytest.fixture
def registrar(client_for):
    return client_for(["tenant_admin"])


@pytest.fixture
def student(tenant_id):
    family = Family.objects.create(tenant_id=tenant_id, name="Tran Household")
    s = Student.objects.create(
        tenant_id=tenant_id, family=family, first_name="Mia", last_name="Tran",
        year_level=8, enrolment_status="enrolled", student_number="S1001",
        date_of_birth=date(2012, 4, 3),
    )
    section = ClassSection.objects.create(tenant_id=tenant_id, name="8A", year_level=8)
    Enrolment.objects.create(
        tenant_id=tenant_id, student=s, class_section=section, status="active"
    )
    return s


def _owe(tenant_id, student, amount="500.00"):
    plan = FeePlan.objects.create(
        tenant_id=tenant_id, name="Termly", schedule_type="upfront", installments_count=1
    )
    bill = StudentBill.objects.create(
        tenant_id=tenant_id, student=student, plan=plan, status="draft"
    )
    BillLineItem.objects.create(
        tenant_id=tenant_id, bill=bill, category="tuition", amount=Decimal(amount)
    )
    generate_installments(bill)
    return bill


# ── exit checks ──────────────────────────────────────────────────────────────
@pytest.mark.django_db
def test_a_clear_student_passes_every_check(registrar, student):
    resp = registrar.get(f"/api/v1/sis/students/{student.id}/exit-checks/")
    assert resp.status_code == 200
    assert resp.data["clear"] is True


@pytest.mark.django_db
def test_outstanding_fees_show_up_as_a_named_check(registrar, tenant_id, student):
    """The registrar needs to know *which* thing to chase, not just 'blocked'."""
    _owe(tenant_id, student)
    resp = registrar.get(f"/api/v1/sis/students/{student.id}/exit-checks/")
    assert resp.data["clear"] is False
    fees = next(c for c in resp.data["checks"] if c["check"] == "fees")
    assert fees["passed"] is False
    assert "500" in fees["detail"]


@pytest.mark.django_db
def test_unreturned_books_block_too(registrar, tenant_id, student):
    book = Book.objects.create(tenant_id=tenant_id, title="Borrowed", copies_total=1)
    Loan.objects.create(
        tenant_id=tenant_id, book=book, student=student, status="borrowed",
        due_on=timezone.localdate(),
    )
    resp = registrar.get(f"/api/v1/sis/students/{student.id}/exit-checks/")
    library = next(c for c in resp.data["checks"] if c["check"] == "library")
    assert library["passed"] is False


# ── exiting ──────────────────────────────────────────────────────────────────
@pytest.mark.django_db
def test_exiting_closes_class_enrolments(registrar, tenant_id, student):
    resp = registrar.post(f"/api/v1/sis/students/{student.id}/exit/", {
        "reason": "Family relocated", "destination": "Northside High",
    }, format="json")
    assert resp.status_code == 200, resp.data

    student.refresh_from_db()
    assert student.enrolment_status == "withdrawn"
    assert student.exit_destination == "Northside High"
    assert not Enrolment.objects.filter(student=student, status="active").exists()


@pytest.mark.django_db
def test_graduating_is_distinct_from_withdrawing(registrar, student):
    """A system that records every leaver identically cannot produce alumni."""
    registrar.post(f"/api/v1/sis/students/{student.id}/exit/", {
        "reason": "Completed Year 12", "graduated": True,
    }, format="json")
    student.refresh_from_db()
    assert student.enrolment_status == "graduated"


@pytest.mark.django_db
def test_a_debt_blocks_the_exit_until_overridden(registrar, tenant_id, student):
    """Letting a student walk out silently is how a debt becomes unrecoverable."""
    _owe(tenant_id, student)
    blocked = registrar.post(f"/api/v1/sis/students/{student.id}/exit/", {
        "reason": "Moving"
    }, format="json")
    assert blocked.status_code == 409
    assert "fees" in blocked.data["detail"]

    forced = registrar.post(f"/api/v1/sis/students/{student.id}/exit/", {
        "reason": "Moving", "override_reason": "Debt referred to collections",
    }, format="json")
    assert forced.status_code == 200


@pytest.mark.django_db
def test_settling_the_account_unblocks_the_exit(registrar, tenant_id, student):
    bill = _owe(tenant_id, student)
    for installment in bill.installments.all():
        record_payment(installment, amount=installment.balance)

    resp = registrar.post(f"/api/v1/sis/students/{student.id}/exit/", {
        "reason": "Moving"
    }, format="json")
    assert resp.status_code == 200


@pytest.mark.django_db
def test_exiting_twice_is_refused(registrar, student):
    registrar.post(f"/api/v1/sis/students/{student.id}/exit/", {"reason": "Moving"}, format="json")
    again = registrar.post(
        f"/api/v1/sis/students/{student.id}/exit/", {"reason": "Moving"}, format="json"
    )
    assert again.status_code == 409


@pytest.mark.django_db
def test_exiting_cancels_transport(registrar, tenant_id, student):
    from products.cyed.transport.models import Bus, TransportSubscription, TransportZone

    zone = TransportZone.objects.create(tenant_id=tenant_id, name="Zone 1", base_fee=Decimal("300"))
    bus = Bus.objects.create(tenant_id=tenant_id, identifier="Bus #12", rego="ABC123", capacity=40)
    sub = TransportSubscription.objects.create(
        tenant_id=tenant_id, student=student, zone=zone, assigned_bus=bus,
        status="active", fee_amount=Decimal("300"),
    )
    registrar.post(f"/api/v1/sis/students/{student.id}/exit/", {"reason": "Moving"}, format="json")
    sub.refresh_from_db()
    assert sub.status == "cancelled"


@pytest.mark.django_db
def test_the_last_child_leaving_closes_the_households_dunning_case(
    registrar, tenant_id, student
):
    """A family with no children left should stop receiving fee letters."""
    from products.cyed.billing.models import DunningCase

    case = DunningCase.objects.create(
        tenant_id=tenant_id, family=student.family, stage=1, status="open",
        opened_on=timezone.localdate(), opening_balance=Decimal("100"),
    )
    registrar.post(f"/api/v1/sis/students/{student.id}/exit/", {
        "reason": "Moving", "override_reason": "Debt referred",
    }, format="json")
    case.refresh_from_db()
    assert case.status == "resolved"


# ── Transfer Certificates ────────────────────────────────────────────────────
@pytest.mark.django_db
def test_a_certificate_cannot_be_issued_before_the_student_leaves(registrar, student):
    resp = registrar.post(
        f"/api/v1/sis/students/{student.id}/transfer-certificate/", {}, format="json"
    )
    assert resp.status_code == 409
    assert "Exit the student" in resp.data["detail"]


@pytest.mark.django_db
def test_a_certificate_records_the_facts_at_issue(registrar, student):
    registrar.post(f"/api/v1/sis/students/{student.id}/exit/", {
        "reason": "Family relocated", "destination": "Northside High",
    }, format="json")
    resp = registrar.post(
        f"/api/v1/sis/students/{student.id}/transfer-certificate/", {}, format="json"
    )
    assert resp.status_code == 201, resp.data
    assert resp.data["version"] == 1
    assert resp.data["fees_settled"] is True

    snapshot = resp.data["snapshot"]
    assert snapshot["student"]["name"] == "Mia Tran"
    assert snapshot["student"]["student_number"] == "S1001"
    assert snapshot["enrolment"]["destination"] == "Northside High"


@pytest.mark.django_db
def test_a_certificate_is_not_issued_over_an_unpaid_balance(registrar, tenant_id, student):
    """The certificate asserts good standing — that is a statement, not a form."""
    _owe(tenant_id, student)
    registrar.post(f"/api/v1/sis/students/{student.id}/exit/", {
        "reason": "Moving", "override_reason": "Debt referred",
    }, format="json")

    resp = registrar.post(
        f"/api/v1/sis/students/{student.id}/transfer-certificate/", {}, format="json"
    )
    assert resp.status_code == 409
    assert "good standing" in resp.data["detail"]


@pytest.mark.django_db
def test_reissuing_mints_a_new_version_and_keeps_the_old(registrar, student):
    registrar.post(f"/api/v1/sis/students/{student.id}/exit/", {"reason": "Moving"}, format="json")
    first = registrar.post(
        f"/api/v1/sis/students/{student.id}/transfer-certificate/", {}, format="json"
    )
    second = registrar.post(
        f"/api/v1/sis/students/{student.id}/transfer-certificate/", {}, format="json"
    )
    assert first.data["version"] == 1
    assert second.data["version"] == 2
    assert TransferCertificate.objects.filter(student=student).count() == 2


@pytest.mark.django_db
def test_the_snapshot_survives_later_edits_to_the_student(registrar, student):
    """A certificate reissued next year must still say what it said."""
    registrar.post(f"/api/v1/sis/students/{student.id}/exit/", {"reason": "Moving"}, format="json")
    issued = registrar.post(
        f"/api/v1/sis/students/{student.id}/transfer-certificate/", {}, format="json"
    )
    student.last_name = "Changed"
    student.save(update_fields=["last_name"])

    certificate = TransferCertificate.objects.get(id=issued.data["certificate"])
    assert certificate.snapshot["student"]["name"] == "Mia Tran"


# ── alumni ───────────────────────────────────────────────────────────────────
@pytest.mark.django_db
def test_alumni_lists_leavers_most_recent_first(registrar, tenant_id, student):
    other = Student.objects.create(
        tenant_id=tenant_id, first_name="Old", last_name="Leaver",
        year_level=12, enrolment_status="graduated",
        exit_date=timezone.localdate() - timedelta(days=400),
    )
    registrar.post(f"/api/v1/sis/students/{student.id}/exit/", {
        "reason": "Family relocated", "graduated": True,
    }, format="json")

    resp = registrar.get("/api/v1/sis/students/alumni/")
    assert resp.status_code == 200
    assert resp.data["count"] == 2
    assert resp.data["results"][0]["name"] == "Mia Tran"
    assert resp.data["results"][1]["student"] == str(other.id)


@pytest.mark.django_db
def test_alumni_carries_the_graduated_withdrawn_distinction(registrar, tenant_id, student):
    registrar.post(f"/api/v1/sis/students/{student.id}/exit/", {
        "reason": "Family relocated"
    }, format="json")
    rows = alumni(tenant_id)
    assert rows[0]["status"] == "withdrawn"
    assert rows[0]["exit_reason"] == "Family relocated"


@pytest.mark.django_db
def test_enrolled_students_are_not_alumni(registrar, tenant_id, student):
    assert alumni(tenant_id) == []
