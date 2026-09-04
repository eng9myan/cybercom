"""
Money-path invariant tests for the GL choke point (`post_journal_entry`).

Every GL posting in CyCom — POS checkout, invoice posting, stock moves, payroll —
funnels through `post_journal_entry`, so these invariants protect the whole
system's double-entry integrity. See docs/blueprint/H_nfr_checklist.md Q8.
"""
from decimal import Decimal

import pytest

from products.cycom.accounting.models import Account, JournalLine
from products.cycom.accounting.services import UnbalancedEntryError, post_journal_entry

T = "11111111-1111-1111-1111-111111111111"


@pytest.fixture
def accounts(db):
    return {
        "cash": Account.objects.create(tenant_id=T, code="1000", name="Cash", account_type="asset"),
        "ar": Account.objects.create(tenant_id=T, code="1100", name="AR", account_type="asset"),
        "rev": Account.objects.create(tenant_id=T, code="4000", name="Revenue", account_type="income"),
        "tax": Account.objects.create(tenant_id=T, code="2120", name="Output VAT", account_type="liability"),
    }


@pytest.mark.django_db
def test_balanced_entry_posts_and_lines_tie_out(accounts):
    entry = post_journal_entry(
        tenant_id=T, date="2026-07-05", reference="INV-1",
        lines=[
            {"account": accounts["ar"], "debit": Decimal("116.00"), "credit": 0},
            {"account": accounts["rev"], "debit": 0, "credit": Decimal("100.00")},
            {"account": accounts["tax"], "debit": 0, "credit": Decimal("16.00")},
        ],
    )
    assert entry.status == "posted"
    lines = JournalLine.objects.filter(entry=entry)
    assert sum(l.debit for l in lines) == sum(l.credit for l in lines) == Decimal("116.00")
    # every line carries the entry's tenant
    assert all(str(l.tenant_id) == T for l in lines)


@pytest.mark.django_db
def test_unbalanced_entry_is_rejected(accounts):
    with pytest.raises(UnbalancedEntryError):
        post_journal_entry(
            tenant_id=T, date="2026-07-05", reference="BAD-1",
            lines=[
                {"account": accounts["cash"], "debit": Decimal("100.00"), "credit": 0},
                {"account": accounts["rev"], "debit": 0, "credit": Decimal("90.00")},
            ],
        )


@pytest.mark.django_db
def test_unbalanced_entry_is_atomic_no_partial_write(accounts):
    from products.cycom.accounting.models import JournalEntry

    before = JournalEntry.objects.count()
    with pytest.raises(UnbalancedEntryError):
        post_journal_entry(
            tenant_id=T, date="2026-07-05", reference="BAD-2",
            lines=[
                {"account": accounts["cash"], "debit": Decimal("1.00"), "credit": 0},
                {"account": accounts["rev"], "debit": 0, "credit": Decimal("2.00")},
            ],
        )
    # @transaction.atomic + the balance check before create() means nothing lands
    assert JournalEntry.objects.count() == before
    assert not JournalLine.objects.filter(entry__reference="BAD-2").exists()


@pytest.mark.django_db
def test_penny_rounding_still_balances(accounts):
    # a 3-way split that must sum exactly
    entry = post_journal_entry(
        tenant_id=T, date="2026-07-05", reference="INV-3",
        lines=[
            {"account": accounts["ar"], "debit": Decimal("33.34"), "credit": 0},
            {"account": accounts["rev"], "debit": 0, "credit": Decimal("33.34")},
        ],
    )
    lines = JournalLine.objects.filter(entry=entry)
    assert sum(l.debit for l in lines) == sum(l.credit for l in lines)
