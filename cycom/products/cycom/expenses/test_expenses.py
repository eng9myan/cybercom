import uuid
from datetime import date
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from products.cycom.accounting.models import Account
from products.cycom.expenses.models import Expense


@pytest.fixture
def platform_admin_client(mint_token, mock_jwks, tenant_id):
    token = mint_token(
        {
            "sub": str(uuid.uuid4()),
            "email": "admin@cybercom.io",
            "tenant_id": str(tenant_id),
            "realm_access": {"roles": ["platform_admin"]},
        }
    )
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


@pytest.fixture
def accounts(db, tenant_id):
    expense_acct = Account.objects.create(
        tenant_id=tenant_id, code="6100", name="Travel Expense", account_type="expense"
    )
    payable_acct = Account.objects.create(
        tenant_id=tenant_id, code="2100", name="Employee Reimbursements Payable", account_type="liability"
    )
    return expense_acct, payable_acct


@pytest.mark.django_db
def test_submit_approve_posts_balanced_gl_entry(platform_admin_client, tenant_id, accounts):
    expense_acct, payable_acct = accounts
    expense = Expense.objects.create(
        tenant_id=tenant_id,
        employee_name="Jane Doe",
        category="Travel",
        amount=Decimal("150.00"),
        expense_date=date.today(),
        expense_account=expense_acct,
        payable_account=payable_acct,
    )

    resp = platform_admin_client.post(f"/api/v1/expenses/expenses/{expense.id}/submit/")
    assert resp.status_code == 200
    assert resp.data["status"] == "submitted"

    resp = platform_admin_client.post(f"/api/v1/expenses/expenses/{expense.id}/approve/")
    assert resp.status_code == 200
    assert resp.data["status"] == "posted"

    expense.refresh_from_db()
    entry = expense.journal_entry
    assert entry is not None
    lines = list(entry.lines.all())
    assert sum(l.debit for l in lines) == sum(l.credit for l in lines) == Decimal("150.00")


@pytest.mark.django_db
def test_cannot_approve_draft_expense(platform_admin_client, tenant_id, accounts):
    expense_acct, payable_acct = accounts
    expense = Expense.objects.create(
        tenant_id=tenant_id,
        employee_name="Jane Doe",
        category="Travel",
        amount=Decimal("50.00"),
        expense_date=date.today(),
        expense_account=expense_acct,
        payable_account=payable_acct,
    )
    resp = platform_admin_client.post(f"/api/v1/expenses/expenses/{expense.id}/approve/")
    assert resp.status_code == 400
