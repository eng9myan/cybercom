"""Multi-company reporting — opt-in: company is nullable everywhere, so a
tenant that never creates a Company sees zero behavior change (covered by
every pre-existing accounting test still passing untouched)."""

from decimal import Decimal

import pytest

from products.cycom.accounting.models import Account
from products.cycom.accounting.reports import profit_and_loss, trial_balance
from products.cycom.accounting.services import post_journal_entry
from products.cycom.company.models import Company

T = "44444444-4444-4444-4444-444444444444"


@pytest.fixture
def accounts(db):
    return {
        "cash": Account.objects.create(tenant_id=T, code="1000", name="Cash", account_type="asset"),
        "equity": Account.objects.create(tenant_id=T, code="3000", name="Equity", account_type="equity"),
        "rev": Account.objects.create(tenant_id=T, code="4000", name="Revenue", account_type="income"),
    }


@pytest.fixture
def companies(db):
    return {
        "jo": Company.objects.create(tenant_id=T, name="Acme Jordan"),
        "sa": Company.objects.create(tenant_id=T, name="Acme Saudi"),
    }


@pytest.mark.django_db
def test_unscoped_entry_has_null_company(accounts):
    entry = post_journal_entry(
        tenant_id=T, date="2026-05-01", reference="NO-COMPANY",
        lines=[
            {"account": accounts["cash"], "debit": Decimal("100"), "credit": 0},
            {"account": accounts["rev"], "debit": 0, "credit": Decimal("100")},
        ],
    )
    assert entry.company_id is None


@pytest.mark.django_db
def test_company_scoped_report_only_sees_its_own_entries(accounts, companies):
    post_journal_entry(
        tenant_id=T, date="2026-05-01", reference="JO-SALE", company=companies["jo"],
        lines=[
            {"account": accounts["cash"], "debit": Decimal("500"), "credit": 0},
            {"account": accounts["rev"], "debit": 0, "credit": Decimal("500")},
        ],
    )
    post_journal_entry(
        tenant_id=T, date="2026-05-02", reference="SA-SALE", company=companies["sa"],
        lines=[
            {"account": accounts["cash"], "debit": Decimal("300"), "credit": 0},
            {"account": accounts["rev"], "debit": 0, "credit": Decimal("300")},
        ],
    )

    jo_pl = profit_and_loss(T, company=companies["jo"])
    assert jo_pl["total_income"] == Decimal("500.00")

    sa_pl = profit_and_loss(T, company=companies["sa"])
    assert sa_pl["total_income"] == Decimal("300.00")


@pytest.mark.django_db
def test_omitting_company_consolidates_across_all(accounts, companies):
    post_journal_entry(
        tenant_id=T, date="2026-05-01", reference="JO-SALE", company=companies["jo"],
        lines=[
            {"account": accounts["cash"], "debit": Decimal("500"), "credit": 0},
            {"account": accounts["rev"], "debit": 0, "credit": Decimal("500")},
        ],
    )
    post_journal_entry(
        tenant_id=T, date="2026-05-02", reference="SA-SALE", company=companies["sa"],
        lines=[
            {"account": accounts["cash"], "debit": Decimal("300"), "credit": 0},
            {"account": accounts["rev"], "debit": 0, "credit": Decimal("300")},
        ],
    )
    unscoped = post_journal_entry(
        tenant_id=T, date="2026-05-03", reference="NO-COMPANY",
        lines=[
            {"account": accounts["cash"], "debit": Decimal("50"), "credit": 0},
            {"account": accounts["rev"], "debit": 0, "credit": Decimal("50")},
        ],
    )
    assert unscoped.company_id is None

    consolidated = profit_and_loss(T)
    assert consolidated["total_income"] == Decimal("850.00")  # 500 + 300 + 50


@pytest.mark.django_db
def test_trial_balance_company_scoped_still_balances(accounts, companies):
    post_journal_entry(
        tenant_id=T, date="2026-05-01", reference="JO-CAPITAL", company=companies["jo"],
        lines=[
            {"account": accounts["cash"], "debit": Decimal("1000"), "credit": 0},
            {"account": accounts["equity"], "debit": 0, "credit": Decimal("1000")},
        ],
    )
    tb = trial_balance(T, company=companies["jo"])
    assert tb["balanced"] is True
    assert tb["total_debit"] == Decimal("1000.00")
