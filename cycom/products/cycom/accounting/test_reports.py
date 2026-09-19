"""
Coverage for the financial-statement functions in reports.py — they had zero
direct tests despite computing what auditors and lenders actually read.
"""
from decimal import Decimal

import pytest

from products.cycom.accounting.models import Account
from products.cycom.accounting.reports import (
    balance_sheet,
    profit_and_loss,
    trial_balance,
    vat_return,
)
from products.cycom.accounting.services import post_journal_entry

T = "22222222-2222-2222-2222-222222222222"


@pytest.fixture
def accounts(db):
    return {
        "cash": Account.objects.create(tenant_id=T, code="1000", name="Cash", account_type="asset"),
        "ar": Account.objects.create(tenant_id=T, code="1100", name="AR", account_type="asset"),
        "equity": Account.objects.create(tenant_id=T, code="3000", name="Owner Equity", account_type="equity"),
        "rev": Account.objects.create(tenant_id=T, code="4000", name="Revenue", account_type="income"),
        "cogs": Account.objects.create(tenant_id=T, code="5000", name="COGS", account_type="expense"),
        "output_vat": Account.objects.create(tenant_id=T, code="2120", name="Output VAT", account_type="liability"),
        "input_vat": Account.objects.create(tenant_id=T, code="1150", name="Input VAT", account_type="asset"),
        "ap": Account.objects.create(tenant_id=T, code="2000", name="AP", account_type="liability"),
    }


@pytest.fixture
def posted_period(accounts):
    """Owner funds the business, then one sale and one purchase in the period."""
    post_journal_entry(
        tenant_id=T, date="2026-07-01", reference="CAPITAL",
        lines=[
            {"account": accounts["cash"], "debit": Decimal("1000.00"), "credit": 0},
            {"account": accounts["equity"], "debit": 0, "credit": Decimal("1000.00")},
        ],
    )
    post_journal_entry(
        tenant_id=T, date="2026-07-05", reference="SALE-1",
        lines=[
            {"account": accounts["ar"], "debit": Decimal("116.00"), "credit": 0},
            {"account": accounts["rev"], "debit": 0, "credit": Decimal("100.00")},
            {"account": accounts["output_vat"], "debit": 0, "credit": Decimal("16.00")},
        ],
    )
    post_journal_entry(
        tenant_id=T, date="2026-07-10", reference="PURCHASE-1",
        lines=[
            {"account": accounts["cogs"], "debit": Decimal("40.00"), "credit": 0},
            {"account": accounts["input_vat"], "debit": Decimal("6.40"), "credit": 0},
            {"account": accounts["ap"], "debit": 0, "credit": Decimal("46.40")},
        ],
    )
    # a draft entry must never leak into any statement
    from products.cycom.accounting.models import JournalEntry, JournalLine

    draft = JournalEntry.objects.create(tenant_id=T, date="2026-07-15", reference="DRAFT-1", status="draft")
    JournalLine.objects.create(tenant_id=T, entry=draft, account=accounts["cash"], debit=Decimal("9999.00"))
    JournalLine.objects.create(tenant_id=T, entry=draft, account=accounts["equity"], credit=Decimal("9999.00"))
    return accounts


@pytest.mark.django_db
def test_trial_balance_ties_out(posted_period):
    tb = trial_balance(T, date_to="2026-07-31")
    assert tb["balanced"] is True
    assert tb["total_debit"] == tb["total_credit"]
    codes = {r["code"] for r in tb["lines"]}
    assert "1000" in codes and "4000" in codes
    # the draft entry's 9999 must not appear anywhere in the totals
    assert tb["total_debit"] < Decimal("2000.00")


@pytest.mark.django_db
def test_trial_balance_omits_zero_balance_accounts(posted_period, accounts):
    Account.objects.create(tenant_id=T, code="6000", name="Unused", account_type="expense")
    tb = trial_balance(T, date_to="2026-07-31")
    assert "6000" not in {r["code"] for r in tb["lines"]}


@pytest.mark.django_db
def test_profit_and_loss_net_profit(posted_period):
    pl = profit_and_loss(T, date_from="2026-07-01", date_to="2026-07-31")
    assert pl["total_income"] == Decimal("100.00")
    assert pl["total_expenses"] == Decimal("40.00")
    assert pl["net_profit"] == Decimal("60.00")


@pytest.mark.django_db
def test_profit_and_loss_respects_date_window(posted_period, accounts):
    post_journal_entry(
        tenant_id=T, date="2026-08-01", reference="SALE-NEXT-MONTH",
        lines=[
            {"account": accounts["ar"], "debit": Decimal("50.00"), "credit": 0},
            {"account": accounts["rev"], "debit": 0, "credit": Decimal("50.00")},
        ],
    )
    pl = profit_and_loss(T, date_from="2026-07-01", date_to="2026-07-31")
    assert pl["total_income"] == Decimal("100.00")  # August sale excluded


@pytest.mark.django_db
def test_balance_sheet_balances_with_current_period_earnings(posted_period):
    bs = balance_sheet(T, date_to="2026-07-31")
    assert bs["balanced"] is True
    assert bs["current_period_earnings"] == Decimal("60.00")
    assert bs["total_assets"] == bs["total_liabilities_and_equity"]


@pytest.mark.django_db
def test_balance_sheet_asset_breakdown(posted_period):
    bs = balance_sheet(T, date_to="2026-07-31")
    by_code = {r["code"]: r["amount"] for r in bs["assets"]}
    # cash: +1000 capital, -0 (AR/VAT unaffected); AR: +116; input VAT: +6.40
    assert by_code["1000"] == Decimal("1000.00")
    assert by_code["1100"] == Decimal("116.00")
    assert by_code["1150"] == Decimal("6.40")


@pytest.mark.django_db
def test_vat_return_net_payable(posted_period):
    vr = vat_return(T, date_from="2026-07-01", date_to="2026-07-31")
    assert vr["output_tax"] == Decimal("16.00")
    assert vr["input_tax"] == Decimal("6.40")
    assert vr["net_payable"] == Decimal("9.60")


@pytest.mark.django_db
def test_reports_are_tenant_isolated(posted_period, accounts):
    other_tenant = "33333333-3333-3333-3333-333333333333"
    other_cash = Account.objects.create(tenant_id=other_tenant, code="1000", name="Cash", account_type="asset")
    other_rev = Account.objects.create(tenant_id=other_tenant, code="4000", name="Revenue", account_type="income")
    post_journal_entry(
        tenant_id=other_tenant, date="2026-07-05", reference="OTHER-SALE",
        lines=[
            {"account": other_cash, "debit": Decimal("500.00"), "credit": 0},
            {"account": other_rev, "debit": 0, "credit": Decimal("500.00")},
        ],
    )
    pl = profit_and_loss(T, date_from="2026-07-01", date_to="2026-07-31")
    assert pl["total_income"] == Decimal("100.00")  # unaffected by the other tenant's 500
