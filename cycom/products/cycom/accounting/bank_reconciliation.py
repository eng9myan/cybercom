"""
Bank reconciliation: match imported bank-statement lines against posted
JournalLines on the same account, and report what's still open on each side.

Standard reconciliation identity this module enforces:
    adjusted_book_balance  = cleared_balance + unmatched_statement_total
    adjusted_bank_balance  = statement_ending_balance + outstanding_total
    difference = adjusted_book_balance - statement_ending_balance
               = (cleared_balance + unmatched_statement_total) - statement_ending_balance
A reconciliation is complete when difference == 0 (given the true bank ending
balance) — everything else in this module exists to get there without
trusting a human to eyeball a spreadsheet.
"""
from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from products.cycom.accounting.models import BankStatementLine, JournalLine

Z = Decimal("0.00")

# How far apart a bank-cleared date and the book-entry date may be for
# auto-match to consider them the same transaction (a cheque can take a
# while to clear; a card settlement usually doesn't).
AUTO_MATCH_WINDOW_DAYS = 10


def _line_amount(line: JournalLine) -> Decimal:
    return line.debit - line.credit


def import_statement_lines(tenant_id, *, bank_account, rows):
    """
    rows: iterable of dicts {statement_date, description, amount, external_ref?}
    Skips rows that already exist for this (bank_account, statement_date,
    amount, external_ref) — re-uploading the same statement is idempotent.
    Returns {created: [...], skipped_duplicates: int}.
    """
    created = []
    skipped = 0
    for row in rows:
        external_ref = row.get("external_ref", "")
        dupe_filter = dict(
            tenant_id=tenant_id, bank_account=bank_account,
            statement_date=row["statement_date"], amount=Decimal(str(row["amount"])),
        )
        if external_ref:
            dupe_filter["external_ref"] = external_ref
        if BankStatementLine.objects.filter(**dupe_filter).exists():
            skipped += 1
            continue
        created.append(BankStatementLine.objects.create(
            tenant_id=tenant_id,
            bank_account=bank_account,
            statement_date=row["statement_date"],
            description=row.get("description", ""),
            amount=Decimal(str(row["amount"])),
            external_ref=external_ref,
        ))
    return {"created": created, "skipped_duplicates": skipped}


def match_line(tenant_id, *, statement_line_id, journal_line_id):
    """Manually pair one statement line with one journal line. Refuses a
    mismatch on tenant, account or amount rather than silently reconciling
    the wrong thing — a bank reconciliation that can be wrong is worthless."""
    try:
        statement_line = BankStatementLine.objects.get(pk=statement_line_id, tenant_id=tenant_id)
    except BankStatementLine.DoesNotExist:
        raise ValidationError("Statement line not found.")
    if statement_line.is_reconciled:
        raise ValidationError("Statement line is already reconciled.")

    try:
        journal_line = JournalLine.objects.select_related("entry").get(
            pk=journal_line_id, tenant_id=tenant_id
        )
    except JournalLine.DoesNotExist:
        raise ValidationError("Journal line not found.")

    if journal_line.entry.status != "posted":
        raise ValidationError("Cannot reconcile against a draft entry.")
    if journal_line.account_id != statement_line.bank_account_id:
        raise ValidationError("Journal line is not on this statement's bank account.")
    if BankStatementLine.objects.filter(
        matched_line_id=journal_line.id, is_reconciled=True
    ).exclude(pk=statement_line.pk).exists():
        raise ValidationError("Journal line is already matched to another statement line.")
    if _line_amount(journal_line) != statement_line.amount:
        raise ValidationError(
            f"Amount mismatch: statement {statement_line.amount} vs ledger {_line_amount(journal_line)}."
        )

    statement_line.matched_line = journal_line
    statement_line.is_reconciled = True
    statement_line.reconciled_at = timezone.now()
    statement_line.save(update_fields=["matched_line", "is_reconciled", "reconciled_at", "updated_at"])
    return statement_line


def unmatch_line(tenant_id, *, statement_line_id):
    try:
        statement_line = BankStatementLine.objects.get(pk=statement_line_id, tenant_id=tenant_id)
    except BankStatementLine.DoesNotExist:
        raise ValidationError("Statement line not found.")
    statement_line.matched_line = None
    statement_line.is_reconciled = False
    statement_line.reconciled_at = None
    statement_line.save(update_fields=["matched_line", "is_reconciled", "reconciled_at", "updated_at"])
    return statement_line


@transaction.atomic
def auto_match(tenant_id, *, bank_account_id):
    """
    Exact-amount match: an unreconciled statement line auto-matches a posted,
    unmatched journal line on the same account with the identical signed
    amount, within AUTO_MATCH_WINDOW_DAYS of the statement date — but only
    when exactly one such candidate exists. An ambiguous amount (e.g. two
    $50 deposits the same week) is left for a human rather than guessed.
    """
    already_matched_line_ids = set(
        BankStatementLine.objects.filter(
            tenant_id=tenant_id, bank_account_id=bank_account_id, is_reconciled=True
        ).values_list("matched_line_id", flat=True)
    )
    candidates = list(
        JournalLine.objects.filter(
            tenant_id=tenant_id, account_id=bank_account_id, entry__status="posted",
        ).exclude(id__in=already_matched_line_ids).select_related("entry")
    )

    matched = 0
    ambiguous = 0
    unresolved_lines = list(
        BankStatementLine.objects.filter(
            tenant_id=tenant_id, bank_account_id=bank_account_id, is_reconciled=False,
        )
    )
    for statement_line in unresolved_lines:
        window_start = statement_line.statement_date - timedelta(days=AUTO_MATCH_WINDOW_DAYS)
        window_end = statement_line.statement_date + timedelta(days=AUTO_MATCH_WINDOW_DAYS)
        hits = [
            c for c in candidates
            if _line_amount(c) == statement_line.amount
            and window_start <= c.entry.date <= window_end
        ]
        if len(hits) == 1:
            match_line(tenant_id, statement_line_id=statement_line.id, journal_line_id=hits[0].id)
            candidates.remove(hits[0])
            matched += 1
        elif len(hits) > 1:
            ambiguous += 1

    return {"matched": matched, "ambiguous": ambiguous, "remaining_unmatched": len(unresolved_lines) - matched}


def reconciliation_summary(tenant_id, *, bank_account_id, date_to=None, statement_ending_balance=None):
    ledger_lines = JournalLine.objects.filter(
        tenant_id=tenant_id, account_id=bank_account_id, entry__status="posted",
    ).select_related("entry")
    if date_to:
        ledger_lines = ledger_lines.filter(entry__date__lte=date_to)
    ledger_lines = list(ledger_lines)

    matched_line_ids = set(
        BankStatementLine.objects.filter(
            tenant_id=tenant_id, bank_account_id=bank_account_id, is_reconciled=True,
        ).values_list("matched_line_id", flat=True)
    )

    ledger_balance = sum((_line_amount(l) for l in ledger_lines), Z)
    outstanding = [l for l in ledger_lines if l.id not in matched_line_ids]
    outstanding_total = sum((_line_amount(l) for l in outstanding), Z)
    cleared_balance = ledger_balance - outstanding_total

    statement_lines = BankStatementLine.objects.filter(tenant_id=tenant_id, bank_account_id=bank_account_id)
    if date_to:
        statement_lines = statement_lines.filter(statement_date__lte=date_to)
    unmatched_statement = list(statement_lines.filter(is_reconciled=False))
    unmatched_statement_total = sum((sl.amount for sl in unmatched_statement), Z)

    result = {
        "ledger_balance": ledger_balance,
        "cleared_balance": cleared_balance,
        "outstanding_journal_lines": [
            {"id": l.id, "date": str(l.entry.date), "reference": l.entry.reference,
             "description": l.description, "amount": _line_amount(l)}
            for l in outstanding
        ],
        "outstanding_total": outstanding_total,
        "unmatched_statement_lines": [
            {"id": sl.id, "date": str(sl.statement_date), "description": sl.description,
             "amount": sl.amount}
            for sl in unmatched_statement
        ],
        "unmatched_statement_total": unmatched_statement_total,
        "has_open_items": bool(outstanding) or bool(unmatched_statement),
        "statement_ending_balance": statement_ending_balance,
        "difference": None,
        "is_balanced": None,
    }
    if statement_ending_balance is not None:
        adjusted_book_balance = cleared_balance + unmatched_statement_total
        difference = adjusted_book_balance - Decimal(str(statement_ending_balance))
        result["difference"] = difference
        result["is_balanced"] = difference == Z
    return result
