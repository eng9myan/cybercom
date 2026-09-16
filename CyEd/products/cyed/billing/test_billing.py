import uuid
from datetime import date, timedelta
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from products.cyed.billing.models import BillLineItem, FeePlan, Installment, StudentBill
from products.cyed.billing import services
from products.cyed.notifications.models import Notification
from products.cyed.sis.models import Guardian, Student
from products.cyed.transport.models import TransportSubscription, TransportZone


@pytest.fixture
def client_for(mint_token, mock_jwks, tenant_id):
    def _make(roles, email="user@cyed.edu.au"):
        token = mint_token({"sub": str(uuid.uuid4()), "email": email, "tenant_id": str(tenant_id),
                            "realm_access": {"roles": roles}})
        c = APIClient()
        c.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        return c
    return _make


def _bill(tenant_id, schedule="termly", tuition="3000", transport=None):
    student = Student.objects.create(tenant_id=tenant_id, first_name="Minh", last_name="Nguyen", year_level=8)
    plan = FeePlan.objects.create(tenant_id=tenant_id, name="Termly", schedule_type=schedule, installments_count=3)
    bill = StudentBill.objects.create(tenant_id=tenant_id, student=student, plan=plan, start_date=date(2026, 2, 1))
    BillLineItem.objects.create(tenant_id=tenant_id, bill=bill, category="tuition", amount=Decimal(tuition))
    if transport is not None:
        BillLineItem.objects.create(tenant_id=tenant_id, bill=bill, category="transport", amount=Decimal(transport))
    return student, plan, bill


@pytest.mark.django_db
def test_termly_generates_three_installments(tenant_id):
    _, _, bill = _bill(tenant_id, "termly", tuition="3000")
    services.generate_installments(bill)
    insts = list(bill.installments.order_by("installment_no"))
    assert len(insts) == 3
    assert sum(i.amount_due for i in insts) == Decimal("3000.00")
    assert insts[0].amount_due == Decimal("1000.00")
    # Termly ≈ every 4 months.
    assert insts[1].due_date == date(2026, 6, 1)


@pytest.mark.django_db
def test_upfront_discount(tenant_id):
    student = Student.objects.create(tenant_id=tenant_id, first_name="A", last_name="B", year_level=8)
    plan = FeePlan.objects.create(tenant_id=tenant_id, name="Upfront", schedule_type="upfront",
                                  upfront_discount_percent=Decimal("5"))
    bill = StudentBill.objects.create(tenant_id=tenant_id, student=student, plan=plan, start_date=date(2026, 2, 1))
    BillLineItem.objects.create(tenant_id=tenant_id, bill=bill, category="tuition", amount=Decimal("1000"))
    services.generate_installments(bill)
    insts = list(bill.installments.all())
    assert len(insts) == 1
    assert insts[0].amount_due == Decimal("950.00")  # 5% off


@pytest.mark.django_db
def test_line_item_split_tuition_and_transport(tenant_id):
    _, _, bill = _bill(tenant_id, "termly", tuition="3000", transport="600")
    services.generate_installments(bill)
    assert bill.total_amount == Decimal("3600.00")
    cats = set(bill.line_items.values_list("category", flat=True))
    assert cats == {"tuition", "transport"}


@pytest.mark.django_db
def test_transport_change_reprorates_remaining(tenant_id):
    student, plan, bill = _bill(tenant_id, "termly", tuition="3000")
    services.generate_installments(bill)  # 3 × 1000
    # Pay installment 1.
    i1 = bill.installments.get(installment_no=1)
    services.record_payment(i1, amount=Decimal("1000"))
    assert i1.paid_total == Decimal("1000.00")

    # Add a Full-Trip transport subscription (600) → resync + reprorate.
    zone = TransportZone.objects.create(tenant_id=tenant_id, name="Z", base_fee=600)
    TransportSubscription.objects.create(tenant_id=tenant_id, student=student, zone=zone, trip_type="full_trip",
                                         fee_amount=Decimal("600"))
    services.resync_transport_line(tenant_id, student.id)

    bill.refresh_from_db()
    assert bill.total_amount == Decimal("3600.00")
    # Paid installment untouched; remaining two absorb the extra 600 → (2600/2)=1300 each.
    i2 = bill.installments.get(installment_no=2)
    i3 = bill.installments.get(installment_no=3)
    assert bill.installments.get(installment_no=1).amount_due == Decimal("1000.00")
    assert i2.amount_due + i3.amount_due == Decimal("2600.00")


@pytest.mark.django_db
def test_pay_installment_status(client_for, tenant_id):
    admin = client_for(["tenant_admin"])
    _, _, bill = _bill(tenant_id, "termly", tuition="3000")
    services.generate_installments(bill)
    inst = bill.installments.get(installment_no=1)

    part = admin.post(f"/api/v1/billing/installments/{inst.id}/pay/", {"amount": "400"}, format="json")
    assert part.status_code == 200
    assert part.data["status"] == "partial"
    full = admin.post(f"/api/v1/billing/installments/{inst.id}/pay/", {"amount": "600"}, format="json")
    assert full.data["status"] == "paid"


@pytest.mark.django_db
def test_due_reminders_notify_guardians(tenant_id):
    student, _, bill = _bill(tenant_id, "termly", tuition="3000")
    g = Guardian.objects.create(tenant_id=tenant_id, first_name="Jia", last_name="Nguyen", email="parent@home.com")
    g.students.add(student)
    services.generate_installments(bill, start_date=date.today() + timedelta(days=3))

    sent = services.send_due_reminders(tenant_id, within_days=7)
    assert sent >= 1
    assert Notification.objects.filter(tenant_id=tenant_id, category="billing").count() >= 1


@pytest.mark.django_db
def test_overdue_and_late_fee(tenant_id):
    student = Student.objects.create(tenant_id=tenant_id, first_name="A", last_name="B", year_level=8)
    plan = FeePlan.objects.create(tenant_id=tenant_id, name="Monthly", schedule_type="monthly",
                                  installments_count=1, late_fee_percent=Decimal("10"))
    bill = StudentBill.objects.create(tenant_id=tenant_id, student=student, plan=plan,
                                      start_date=date.today() - timedelta(days=40))
    BillLineItem.objects.create(tenant_id=tenant_id, bill=bill, category="tuition", amount=Decimal("1000"))
    services.generate_installments(bill)

    assert services.mark_overdue(tenant_id) == 1
    assert services.apply_late_fees(tenant_id) == 1
    bill.installments.first().refresh_from_db()
    assert bill.installments.first().amount_due == Decimal("1100.00")  # +10%
