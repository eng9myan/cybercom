import uuid
from datetime import date, timedelta
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from products.cyed.analytics.fee_analytics import compute_fee_risk
from products.cyed.billing import services
from products.cyed.billing.models import BillLineItem, FeePlan, StudentBill
from products.cyed.sis.models import Student


@pytest.fixture
def client_for(mint_token, mock_jwks, tenant_id):
    def _make(roles, email="user@cyed.edu.au"):
        token = mint_token({"sub": str(uuid.uuid4()), "email": email, "tenant_id": str(tenant_id),
                            "realm_access": {"roles": roles}})
        c = APIClient()
        c.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        return c
    return _make


def _bill(tenant_id, start, name="A"):
    student = Student.objects.create(tenant_id=tenant_id, first_name=name, last_name="X", year_level=8)
    plan = FeePlan.objects.create(tenant_id=tenant_id, name="M", schedule_type="monthly", installments_count=2)
    bill = StudentBill.objects.create(tenant_id=tenant_id, student=student, plan=plan, start_date=start)
    BillLineItem.objects.create(tenant_id=tenant_id, bill=bill, category="tuition", amount=Decimal("1000"))
    services.generate_installments(bill)
    return student, bill


@pytest.mark.django_db
def test_fee_risk_bands_and_cashflow(tenant_id):
    # On-track student (future dues).
    _bill(tenant_id, date.today() + timedelta(days=10), "OnTrack")
    # Overdue student → high risk.
    _, overdue_bill = _bill(tenant_id, date.today() - timedelta(days=40), "Late")
    services.mark_overdue(tenant_id)

    result = compute_fee_risk(tenant_id)
    assert result["summary"]["high"] >= 1
    # Cash-flow buckets present and expected <= due.
    cf = result["cashflow"]
    assert Decimal(cf["expected_30"]) <= Decimal(cf["due_30"]) + Decimal("0.01")
    # High-risk students sorted first.
    assert result["students"][0]["risk_band"] == "high"


@pytest.mark.django_db
def test_fee_risk_endpoint_finance_only(client_for, tenant_id):
    _bill(tenant_id, date.today() + timedelta(days=5))
    teacher = client_for(["teacher"])
    assert teacher.get("/api/v1/analytics/fee-risk/").status_code == 403
    finance = client_for(["finance"])
    resp = finance.get("/api/v1/analytics/fee-risk/")
    assert resp.status_code == 200
    assert "cashflow" in resp.data and "students" in resp.data
