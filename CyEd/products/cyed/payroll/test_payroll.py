import uuid
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from products.cyed.hr.models import Contract, Staff
from products.cyed.payroll.services import annual_tax, compute_payslip


@pytest.fixture
def finance(mint_token, mock_jwks, tenant_id):
    token = mint_token({"sub": str(uuid.uuid4()), "email": "f@cyed.edu.au", "tenant_id": str(tenant_id),
                        "realm_access": {"roles": ["finance"]}})
    c = APIClient()
    c.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return c


def test_annual_tax_brackets():
    assert annual_tax(Decimal("18000")) == Decimal("0.00")
    # 45,000 → 16% of (45000-18200) = 4288
    assert annual_tax(Decimal("45000")) == Decimal("4288.00")
    # 90,000 → 4288 + 30% of 45000 = 17788
    assert annual_tax(Decimal("90000")) == Decimal("17788.00")


@pytest.mark.django_db
def test_compute_payslip_super_and_net(tenant_id):
    staff = Staff.objects.create(tenant_id=tenant_id, first_name="Jane", last_name="Doe")
    contract = Contract.objects.create(tenant_id=tenant_id, staff=staff, annual_salary=Decimal("90000"), fte=1)
    calc = compute_payslip(staff=staff, contract=contract)
    assert calc["gross"] == Decimal("7500.00")          # 90000/12
    assert calc["superannuation"] == Decimal("862.50")  # 11.5% of gross
    assert calc["paye_tax"] == Decimal("1482.33")       # 17788/12
    assert calc["net"] == Decimal("6017.67")


@pytest.mark.django_db
def test_payroll_run_process(finance, tenant_id):
    staff = Staff.objects.create(tenant_id=tenant_id, first_name="Jane", last_name="Doe", is_active=True)
    Contract.objects.create(tenant_id=tenant_id, staff=staff, annual_salary=Decimal("60000"), is_current=True)

    run = finance.post("/api/v1/payroll/runs/", {"period_label": "2026-02"}, format="json")
    assert run.status_code == 201, run.data
    processed = finance.post(f"/api/v1/payroll/runs/{run.data['id']}/process/")
    assert processed.status_code == 200
    assert processed.data["status"] == "processed"
    assert len(processed.data["payslips"]) == 1
    assert Decimal(processed.data["payslips"][0]["gross"]) == Decimal("5000.00")


@pytest.mark.django_db
def test_payroll_finance_only(mint_token, mock_jwks, tenant_id):
    token = mint_token({"sub": str(uuid.uuid4()), "email": "t@cyed.edu.au", "tenant_id": str(tenant_id),
                        "realm_access": {"roles": ["teacher"]}})
    c = APIClient()
    c.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    assert c.get("/api/v1/payroll/runs/").status_code == 403
