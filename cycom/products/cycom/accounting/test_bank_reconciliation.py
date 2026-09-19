from datetime import date
from decimal import Decimal

import pytest
from rest_framework.exceptions import ValidationError

from products.cycom.accounting.bank_reconciliation import (
    auto_match,
    import_statement_lines,
    match_line,
    reconciliation_summary,
    unmatch_line,
)
from products.cycom.accounting.models import Account, BankStatementLine
from products.cycom.accounting.services import post_journal_entry

T = "44444444-4444-4444-4444-444444444444"


@pytest.fixture
def accounts(db):
    return {
        "bank": Account.objects.create(tenant_id=T, code="1010", name="Operating Bank", account_type="asset"),
        "rev": Account.objects.create(tenant_id=T, code="4000", name="Revenue", account_type="income"),
        "fees": Account.objects.create(tenant_id=T, code="5900", name="Bank Fees", account_type="expense"),
    }


def _deposit(accounts, amount, d):
    return post_journal_entry(
        tenant_id=T, date=d, reference="DEP",
        lines=[
            {"account": accounts["bank"], "debit": Decimal(amount), "credit": 0},
            {"account": accounts["rev"], "debit": 0, "credit": Decimal(amount)},
        ],
    )


@pytest.mark.django_db
def test_import_is_idempotent_on_duplicates(accounts):
    rows = [{"statement_date": date(2026, 7, 5), "description": "POS deposit",
              "amount": "100.00", "external_ref": "TXN-1"}]
    r1 = import_statement_lines(T, bank_account=accounts["bank"], rows=rows)
    assert len(r1["created"]) == 1
    r2 = import_statement_lines(T, bank_account=accounts["bank"], rows=rows)
    assert len(r2["created"]) == 0
    assert r2["skipped_duplicates"] == 1
    assert BankStatementLine.objects.filter(tenant_id=T).count() == 1


@pytest.mark.django_db
def test_match_line_requires_exact_amount(accounts):
    entry = _deposit(accounts, "100.00", "2026-07-05")
    line = entry.lines.get(account=accounts["bank"])
    stmt = BankStatementLine.objects.create(
        tenant_id=T, bank_account=accounts["bank"], statement_date=date(2026, 7, 5),
        amount=Decimal("99.00"), description="short",
    )
    with pytest.raises(ValidationError):
        match_line(T, statement_line_id=stmt.id, journal_line_id=line.id)


@pytest.mark.django_db
def test_match_and_unmatch_round_trip(accounts):
    entry = _deposit(accounts, "100.00", "2026-07-05")
    line = entry.lines.get(account=accounts["bank"])
    stmt = BankStatementLine.objects.create(
        tenant_id=T, bank_account=accounts["bank"], statement_date=date(2026, 7, 5),
        amount=Decimal("100.00"),
    )
    matched = match_line(T, statement_line_id=stmt.id, journal_line_id=line.id)
    assert matched.is_reconciled is True
    assert matched.matched_line_id == line.id

    with pytest.raises(ValidationError):
        match_line(T, statement_line_id=stmt.id, journal_line_id=line.id)  # already reconciled

    unmatched = unmatch_line(T, statement_line_id=stmt.id)
    assert unmatched.is_reconciled is False
    assert unmatched.matched_line_id is None


@pytest.mark.django_db
def test_match_line_rejects_wrong_account(accounts):
    other_bank = Account.objects.create(tenant_id=T, code="1020", name="Savings", account_type="asset")
    entry = _deposit(accounts, "100.00", "2026-07-05")
    line = entry.lines.get(account=accounts["bank"])
    stmt = BankStatementLine.objects.create(
        tenant_id=T, bank_account=other_bank, statement_date=date(2026, 7, 5),
        amount=Decimal("100.00"),
    )
    with pytest.raises(ValidationError):
        match_line(T, statement_line_id=stmt.id, journal_line_id=line.id)


@pytest.mark.django_db
def test_auto_match_pairs_unambiguous_amounts(accounts):
    e1 = _deposit(accounts, "100.00", "2026-07-05")
    e2 = _deposit(accounts, "250.00", "2026-07-06")
    BankStatementLine.objects.create(
        tenant_id=T, bank_account=accounts["bank"], statement_date=date(2026, 7, 6),
        amount=Decimal("100.00"),
    )
    BankStatementLine.objects.create(
        tenant_id=T, bank_account=accounts["bank"], statement_date=date(2026, 7, 7),
        amount=Decimal("250.00"),
    )
    result = auto_match(T, bank_account_id=accounts["bank"].id)
    assert result["matched"] == 2
    assert BankStatementLine.objects.filter(tenant_id=T, is_reconciled=True).count() == 2


@pytest.mark.django_db
def test_auto_match_skips_ambiguous_duplicate_amounts(accounts):
    _deposit(accounts, "50.00", "2026-07-05")
    _deposit(accounts, "50.00", "2026-07-06")
    BankStatementLine.objects.create(
        tenant_id=T, bank_account=accounts["bank"], statement_date=date(2026, 7, 6),
        amount=Decimal("50.00"),
    )
    result = auto_match(T, bank_account_id=accounts["bank"].id)
    assert result["matched"] == 0
    assert result["ambiguous"] == 1


@pytest.mark.django_db
def test_auto_match_respects_date_window(accounts):
    _deposit(accounts, "100.00", "2026-01-01")  # far outside the window
    BankStatementLine.objects.create(
        tenant_id=T, bank_account=accounts["bank"], statement_date=date(2026, 7, 6),
        amount=Decimal("100.00"),
    )
    result = auto_match(T, bank_account_id=accounts["bank"].id)
    assert result["matched"] == 0


@pytest.mark.django_db
def test_reconciliation_summary_balances_when_matched(accounts):
    entry = _deposit(accounts, "100.00", "2026-07-05")
    line = entry.lines.get(account=accounts["bank"])
    stmt = BankStatementLine.objects.create(
        tenant_id=T, bank_account=accounts["bank"], statement_date=date(2026, 7, 5),
        amount=Decimal("100.00"),
    )
    match_line(T, statement_line_id=stmt.id, journal_line_id=line.id)

    summary = reconciliation_summary(
        T, bank_account_id=accounts["bank"].id, statement_ending_balance="100.00"
    )
    assert summary["cleared_balance"] == Decimal("100.00")
    assert summary["has_open_items"] is False
    assert summary["is_balanced"] is True
    assert summary["difference"] == Decimal("0.00")


@pytest.mark.django_db
def test_reconciliation_summary_flags_outstanding_items(accounts):
    _deposit(accounts, "100.00", "2026-07-05")  # never matched
    BankStatementLine.objects.create(
        tenant_id=T, bank_account=accounts["bank"], statement_date=date(2026, 7, 6),
        amount=Decimal("-12.00"), description="bank fee, not yet booked",
    )
    summary = reconciliation_summary(T, bank_account_id=accounts["bank"].id)
    assert summary["has_open_items"] is True
    assert len(summary["outstanding_journal_lines"]) == 1
    assert summary["outstanding_total"] == Decimal("100.00")
    assert len(summary["unmatched_statement_lines"]) == 1
    assert summary["unmatched_statement_total"] == Decimal("-12.00")


@pytest.mark.django_db
def test_reconciliation_is_tenant_isolated(accounts):
    other_tenant = "55555555-5555-5555-5555-555555555555"
    other_bank = Account.objects.create(tenant_id=other_tenant, code="1010", name="Bank", account_type="asset")
    other_rev = Account.objects.create(tenant_id=other_tenant, code="4000", name="Rev", account_type="income")
    post_journal_entry(
        tenant_id=other_tenant, date="2026-07-05", reference="OTHER",
        lines=[
            {"account": other_bank, "debit": Decimal("9000.00"), "credit": 0},
            {"account": other_rev, "debit": 0, "credit": Decimal("9000.00")},
        ],
    )
    summary = reconciliation_summary(T, bank_account_id=accounts["bank"].id)
    assert summary["ledger_balance"] == Decimal("0.00")
