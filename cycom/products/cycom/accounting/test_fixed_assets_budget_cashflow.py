"""Fixed assets/depreciation, budgeting, and cash-flow statement — Phase 1
of the Odoo gap-closure program. Reuses the accounts/post_journal_entry
fixture convention from test_reports.py."""

import uuid
from datetime import date
from decimal import Decimal

import pytest
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIClient

from products.cycom.accounting.models import Account, Budget, BudgetLine, FixedAsset
from products.cycom.accounting.reports import budget_vs_actual, cash_flow_statement
from products.cycom.accounting.services import post_journal_entry, run_depreciation

T = "33333333-3333-3333-3333-333333333333"


@pytest.fixture
def admin_client(mint_token, mock_jwks):
    token = mint_token(
        {
            "sub": str(uuid.uuid4()),
            "email": "cfo@cybercom.io",
            "tenant_id": T,
            "realm_access": {"roles": ["platform_admin"]},
        }
    )
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


@pytest.fixture
def accounts(db):
    return {
        "cash": Account.objects.create(
            tenant_id=T, code="1000", name="Cash", account_type="asset", cash_flow_type="cash"
        ),
        "equipment": Account.objects.create(
            tenant_id=T, code="1500", name="Equipment", account_type="asset", cash_flow_type="investing"
        ),
        "depr_expense": Account.objects.create(
            tenant_id=T, code="5200", name="Depreciation Expense", account_type="expense",
            cash_flow_type="operating",
        ),
        "accum_depr": Account.objects.create(
            tenant_id=T, code="1510", name="Accumulated Depreciation", account_type="asset",
            cash_flow_type="operating",
        ),
        "revenue": Account.objects.create(
            tenant_id=T, code="4000", name="Revenue", account_type="income", cash_flow_type="operating"
        ),
        "loan": Account.objects.create(
            tenant_id=T, code="2500", name="Bank Loan", account_type="liability", cash_flow_type="financing"
        ),
    }


# ---------------------------------------------------------------------------
# Fixed assets / depreciation
# ---------------------------------------------------------------------------


@pytest.fixture
def asset(db, accounts):
    return FixedAsset.objects.create(
        tenant_id=T,
        name="Delivery Van",
        asset_account=accounts["equipment"],
        depreciation_expense_account=accounts["depr_expense"],
        accumulated_depreciation_account=accounts["accum_depr"],
        acquisition_date="2026-01-01",
        acquisition_cost=Decimal("12000.00"),
        salvage_value=Decimal("0.00"),
        useful_life_months=12,
    )


@pytest.mark.django_db
def test_monthly_depreciation_straight_line(asset):
    assert asset.monthly_depreciation == Decimal("1000.00")


@pytest.mark.django_db
def test_run_depreciation_requires_running_status(asset):
    with pytest.raises(ValidationError):
        run_depreciation(asset, period=date(2026, 1, 1))


@pytest.mark.django_db
def test_run_depreciation_posts_balanced_entry(admin_client, asset):
    admin_client.post(f"/api/v1/accounting/fixed-assets/{asset.id}/activate/")
    asset.refresh_from_db()
    assert asset.status == "running"

    entry = run_depreciation(asset, period=date(2026, 1, 15))
    assert entry.amount == Decimal("1000.00")
    assert entry.period == date(2026, 1, 1)
    assert entry.journal_entry.status == "posted"
    lines = list(entry.journal_entry.lines.all())
    assert sum(l.debit for l in lines) == sum(l.credit for l in lines) == Decimal("1000.00")

    asset.refresh_from_db()
    assert asset.accumulated_depreciation == Decimal("1000.00")
    assert asset.net_book_value == Decimal("11000.00")


@pytest.mark.django_db
def test_cannot_double_depreciate_same_period(asset):
    asset.status = "running"
    asset.save(update_fields=["status"])
    run_depreciation(asset, period=date(2026, 1, 1))
    with pytest.raises(ValidationError):
        run_depreciation(asset, period=date(2026, 1, 20))  # same month


@pytest.mark.django_db
def test_asset_marks_fully_depreciated_on_final_month(asset):
    asset.status = "running"
    asset.save(update_fields=["status"])
    for month in range(1, 13):
        run_depreciation(asset, period=date(2026, month, 1))
    asset.refresh_from_db()
    assert asset.status == "fully_depreciated"
    assert asset.accumulated_depreciation == Decimal("12000.00")
    assert asset.net_book_value == Decimal("0.00")

    with pytest.raises(ValidationError):
        run_depreciation(asset, period=date(2027, 1, 1))


@pytest.mark.django_db
def test_disposed_asset_cannot_depreciate(admin_client, asset):
    asset.status = "running"
    asset.save(update_fields=["status"])
    resp = admin_client.post(f"/api/v1/accounting/fixed-assets/{asset.id}/dispose/")
    assert resp.status_code == 200
    asset.refresh_from_db()
    with pytest.raises(ValidationError):
        run_depreciation(asset, period=date(2026, 2, 1))


# ---------------------------------------------------------------------------
# Budget vs actual
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_budget_vs_actual_ties_to_gl(accounts):
    post_journal_entry(
        tenant_id=T, date="2026-03-05", reference="SALE",
        lines=[
            {"account": accounts["cash"], "debit": Decimal("500.00"), "credit": 0},
            {"account": accounts["revenue"], "debit": 0, "credit": Decimal("500.00")},
        ],
    )
    budget = Budget.objects.create(
        tenant_id=T, name="Q1 2026", fiscal_year=2026, date_from="2026-01-01", date_to="2026-03-31"
    )
    BudgetLine.objects.create(
        tenant_id=T, budget=budget, account=accounts["revenue"], planned_amount=Decimal("600.00")
    )
    result = budget_vs_actual(budget)
    line = result["lines"][0]
    assert line["planned"] == Decimal("600.00")
    assert line["actual"] == Decimal("500.00")
    assert line["variance"] == Decimal("-100.00")
    assert result["total_variance"] == Decimal("-100.00")


# ---------------------------------------------------------------------------
# Cash flow statement
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_cash_flow_categorizes_by_counter_account(accounts):
    # Operating: revenue in cash
    post_journal_entry(
        tenant_id=T, date="2026-04-01", reference="SALE",
        lines=[
            {"account": accounts["cash"], "debit": Decimal("500.00"), "credit": 0},
            {"account": accounts["revenue"], "debit": 0, "credit": Decimal("500.00")},
        ],
    )
    # Investing: buy equipment with cash
    post_journal_entry(
        tenant_id=T, date="2026-04-05", reference="CAPEX",
        lines=[
            {"account": accounts["equipment"], "debit": Decimal("300.00"), "credit": 0},
            {"account": accounts["cash"], "debit": 0, "credit": Decimal("300.00")},
        ],
    )
    # Financing: draw a loan into cash
    post_journal_entry(
        tenant_id=T, date="2026-04-10", reference="LOAN",
        lines=[
            {"account": accounts["cash"], "debit": Decimal("1000.00"), "credit": 0},
            {"account": accounts["loan"], "debit": 0, "credit": Decimal("1000.00")},
        ],
    )

    result = cash_flow_statement(T, date_from=date(2026, 4, 1), date_to=date(2026, 4, 30))
    assert result["operating_activities"] == Decimal("500.00")
    assert result["investing_activities"] == Decimal("-300.00")
    assert result["financing_activities"] == Decimal("1000.00")
    assert result["net_change"] == Decimal("1200.00")
    assert result["closing_balance"] == result["opening_balance"] + result["net_change"]


@pytest.mark.django_db
def test_cash_flow_without_cash_tagged_account_returns_warning(db):
    result = cash_flow_statement(uuid.uuid4())
    assert "warning" in result
    assert result["net_change"] == Decimal("0.00")


@pytest.mark.django_db
def test_cash_flow_opening_balance_from_prior_period(accounts):
    post_journal_entry(
        tenant_id=T, date="2026-01-01", reference="OPENING",
        lines=[
            {"account": accounts["cash"], "debit": Decimal("200.00"), "credit": 0},
            {"account": accounts["revenue"], "debit": 0, "credit": Decimal("200.00")},
        ],
    )
    post_journal_entry(
        tenant_id=T, date="2026-02-01", reference="LATER",
        lines=[
            {"account": accounts["cash"], "debit": Decimal("50.00"), "credit": 0},
            {"account": accounts["revenue"], "debit": 0, "credit": Decimal("50.00")},
        ],
    )
    result = cash_flow_statement(T, date_from=date(2026, 2, 1), date_to=date(2026, 2, 28))
    assert result["opening_balance"] == Decimal("200.00")
    assert result["operating_activities"] == Decimal("50.00")
    assert result["closing_balance"] == Decimal("250.00")
