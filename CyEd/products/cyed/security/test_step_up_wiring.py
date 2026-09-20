"""
RequiresRecentMfa existed (stepup.py, unit-tested) but was wired onto zero
real endpoints — every "sensitive action" it was built to protect was still
reachable on role alone. These tests prove the wiring itself: the four
actions now gated (payroll's two mark-paid actions, budget approval, bank-
statement-period finalisation) refuse without a recent MFA session and
allow through to business logic with one.

Health app is deliberately NOT gated here — see the commit message: its
sensitive actions (administering a dose, closing a sick-bay visit) are
real-time duty-of-care responses, and step-up friction on those would be
a safety regression, not a security improvement.
"""
import uuid
from datetime import date
from decimal import Decimal

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from products.cyed.finance.models import Account, BankStatement, Budget, BudgetLine
from products.cyed.hr.models import Contract, Staff
from products.cyed.payroll.models import PayrollRun, Payslip
from products.cyed.security.models import MfaSession


@pytest.fixture
def finance_client(mint_token, mock_jwks, tenant_id):
    token = mint_token({
        "sub": str(uuid.uuid4()), "email": "finance@cyed.edu.au", "tenant_id": str(tenant_id),
        "realm_access": {"roles": ["finance"]},
    })
    c = APIClient()
    c.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return c


def _grant_recent_mfa(tenant_id, email):
    MfaSession.objects.create(
        tenant_id=tenant_id, user_email=email,
        verified_at=timezone.now(), expires_at=timezone.now() + timezone.timedelta(minutes=15),
    )


@pytest.mark.django_db
def test_payroll_run_mark_paid_requires_recent_mfa(finance_client, tenant_id):
    staff = Staff.objects.create(tenant_id=tenant_id, first_name="Jo", last_name="Ng", is_active=True)
    Contract.objects.create(tenant_id=tenant_id, staff=staff, annual_salary=Decimal("60000"), is_current=True)
    run = PayrollRun.objects.create(tenant_id=tenant_id, period_label="2026-03", status="processed")
    Payslip.objects.create(tenant_id=tenant_id, payroll_run=run, staff=staff, gross=Decimal("5000"))

    denied = finance_client.post(f"/api/v1/payroll/runs/{run.id}/mark-paid/")
    assert denied.status_code == 403

    _grant_recent_mfa(tenant_id, "finance@cyed.edu.au")
    allowed = finance_client.post(f"/api/v1/payroll/runs/{run.id}/mark-paid/")
    assert allowed.status_code == 200
    assert allowed.data["run"] == str(run.id)


@pytest.mark.django_db
def test_payslip_mark_paid_requires_recent_mfa(finance_client, tenant_id):
    staff = Staff.objects.create(tenant_id=tenant_id, first_name="Kai", last_name="Wu", is_active=True)
    run = PayrollRun.objects.create(tenant_id=tenant_id, period_label="2026-03", status="processed")
    slip = Payslip.objects.create(tenant_id=tenant_id, payroll_run=run, staff=staff, gross=Decimal("5000"))

    denied = finance_client.post(f"/api/v1/payroll/payslips/{slip.id}/mark-paid/")
    assert denied.status_code == 403

    _grant_recent_mfa(tenant_id, "finance@cyed.edu.au")
    allowed = finance_client.post(f"/api/v1/payroll/payslips/{slip.id}/mark-paid/")
    assert allowed.status_code == 200


@pytest.mark.django_db
def test_budget_approve_requires_recent_mfa(finance_client, tenant_id):
    account = Account.objects.create(tenant_id=tenant_id, code="4000", name="Tuition", account_type="income")
    budget = Budget.objects.create(tenant_id=tenant_id, name="Ops", fiscal_year="2026")
    BudgetLine.objects.create(tenant_id=tenant_id, budget=budget, account=account, budgeted_amount=Decimal("1000"))

    denied = finance_client.post(f"/api/v1/finance/budgets/{budget.id}/approve/")
    assert denied.status_code == 403
    assert "multi-factor" in str(denied.data.get("detail", "")).lower()

    _grant_recent_mfa(tenant_id, "finance@cyed.edu.au")
    allowed = finance_client.post(f"/api/v1/finance/budgets/{budget.id}/approve/")
    assert allowed.status_code == 200
    assert allowed.data["status"] == "approved"


@pytest.mark.django_db
def test_bank_statement_finalise_requires_recent_mfa(finance_client, tenant_id):
    account = Account.objects.create(tenant_id=tenant_id, code="1000", name="Operating", account_type="asset")
    statement = BankStatement.objects.create(
        tenant_id=tenant_id, account=account,
        period_start=date(2026, 1, 1), period_end=date(2026, 1, 31),
    )

    denied = finance_client.post(f"/api/v1/finance/bank-statements/{statement.id}/finalise/")
    assert denied.status_code == 403

    _grant_recent_mfa(tenant_id, "finance@cyed.edu.au")
    after_mfa = finance_client.post(f"/api/v1/finance/bank-statements/{statement.id}/finalise/")
    # Business rules (statement balances, everything matched) still apply —
    # only the permission layer changes. What matters here is that it's no
    # longer refused for lacking MFA specifically.
    assert after_mfa.status_code != 403


@pytest.mark.django_db
def test_expired_mfa_session_does_not_satisfy_step_up(finance_client, tenant_id):
    staff = Staff.objects.create(tenant_id=tenant_id, first_name="Lu", last_name="Chen", is_active=True)
    run = PayrollRun.objects.create(tenant_id=tenant_id, period_label="2026-04", status="processed")
    Payslip.objects.create(tenant_id=tenant_id, payroll_run=run, staff=staff, gross=Decimal("5000"))

    MfaSession.objects.create(
        tenant_id=tenant_id, user_email="finance@cyed.edu.au",
        verified_at=timezone.now() - timezone.timedelta(hours=1),
        expires_at=timezone.now() - timezone.timedelta(minutes=45),
    )
    resp = finance_client.post(f"/api/v1/payroll/runs/{run.id}/mark-paid/")
    assert resp.status_code == 403
