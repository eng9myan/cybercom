"""
Bank reconciliation: statement import, automatic matching, and the exception
reports an accountant actually works from.

Reconciling by hand means eyeballing a bank statement against the ledger. The
job here is to do the obvious matches automatically, and then present only the
items that need a human — in both directions:

  * bank lines with no ledger entry  → money moved that was never booked
  * ledger entries with no bank line → booked entries the bank never saw

The second direction is the one naive implementations forget, and it is where
the interesting problems hide (a payment recorded twice, a cheque never
presented, a fraudulent entry).
"""

import csv
import io
from datetime import timedelta
from decimal import Decimal, InvalidOperation

from django.db.models import Q
from django.utils import timezone

# How far apart a bank line and a ledger entry may be dated and still be
# considered the same transaction. Banks routinely settle a day or two late.
DATE_TOLERANCE_DAYS = 3


class BankImportError(ValueError):
    """Raised when a statement file cannot be parsed."""


# ── Import ───────────────────────────────────────────────────────────────────
def _parse_amount(row: dict) -> Decimal:
    """
    Australian bank exports are inconsistent: some carry a single signed
    `amount`, others separate `debit`/`credit` columns. Support both, and
    normalise to a signed amount (positive = money in).
    """
    def dec(v):
        v = (v or "").strip().replace("$", "").replace(",", "")
        if not v:
            return None
        neg = v.startswith("(") and v.endswith(")")  # (123.45) = negative
        v = v.strip("()")
        try:
            d = Decimal(v)
        except InvalidOperation:
            raise BankImportError(f"Could not read amount {v!r}")
        return -d if neg else d

    if row.get("amount"):
        return dec(row["amount"])
    debit, credit = dec(row.get("debit")), dec(row.get("credit"))
    if credit is not None and credit != 0:
        return abs(credit)
    if debit is not None and debit != 0:
        return -abs(debit)
    return Decimal("0")


def parse_statement_csv(file_bytes: bytes) -> list[dict]:
    """
    Parse a bank CSV into normalised rows.

    Expected headers (case-insensitive): date, description, and either amount
    or debit/credit. An optional reference column is used for matching.
    """
    try:
        text = file_bytes.decode("utf-8-sig")  # tolerate Excel BOM
    except UnicodeDecodeError:
        text = file_bytes.decode("latin-1")

    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        raise BankImportError("The file has no header row.")

    rows, errors = [], []
    for i, raw in enumerate(reader, start=2):  # row 1 is the header
        row = {(k or "").strip().lower(): (v or "").strip() for k, v in raw.items()}
        if not any(row.values()):
            continue  # blank line
        date = row.get("date") or row.get("transaction date") or row.get("processed date")
        if not date:
            errors.append({"row": i, "error": "missing date"})
            continue
        try:
            amount = _parse_amount(row)
        except BankImportError as exc:
            errors.append({"row": i, "error": str(exc)})
            continue
        rows.append({
            "date": date,
            "description": (row.get("description") or row.get("narrative") or row.get("details") or "")[:255],
            "amount": amount,
            "bank_reference": (row.get("reference") or row.get("bank reference") or "")[:100],
            "_row": i,
        })
    return rows, errors


def import_statement(statement, file_bytes: bytes, *, filename: str = ""):
    """
    Load a CSV into a statement. Idempotent on (date, amount, reference): a
    re-uploaded file will not duplicate lines, because double-importing a
    statement is the fastest way to make a reconciliation lie.
    """
    from products.cyed.finance.models import BankStatementLine

    rows, errors = parse_statement_csv(file_bytes)
    created = duplicates = 0
    for r in rows:
        exists = BankStatementLine.objects.filter(
            tenant_id=statement.tenant_id, statement=statement, date=r["date"],
            amount=r["amount"], bank_reference=r["bank_reference"],
            description=r["description"],
        ).exists()
        if exists:
            duplicates += 1
            continue
        BankStatementLine.objects.create(
            tenant_id=statement.tenant_id, statement=statement, date=r["date"],
            description=r["description"], amount=r["amount"],
            bank_reference=r["bank_reference"],
        )
        created += 1

    if filename:
        statement.source_filename = filename[:255]
        statement.save(update_fields=["source_filename", "updated_at"])

    return {
        "created": created,
        "duplicates_skipped": duplicates,
        "errors": errors,
        "statement_balances": statement.balances,
        "expected_closing": str(statement.expected_closing),
        "declared_closing": str(statement.closing_balance),
    }


# ── Matching ─────────────────────────────────────────────────────────────────
def _entry_amount_for_account(entry, account_id) -> Decimal:
    """Net movement this entry makes on the bank account (signed, + = money in)."""
    total = Decimal("0")
    for line in entry.lines.all():
        if str(line.account_id) == str(account_id):
            total += Decimal(line.debit) - Decimal(line.credit)
    return total


def candidate_entries(line, *, account_id, tolerance_days=DATE_TOLERANCE_DAYS):
    """
    Posted, not-yet-matched journal entries that could be this bank line.

    Scored rather than filtered hard: an exact reference match beats an exact
    amount match, which beats a near date. Returns [(entry, score, reasons)].
    """
    from products.cyed.finance.models import JournalEntry

    window_lo = line.date - timedelta(days=tolerance_days)
    window_hi = line.date + timedelta(days=tolerance_days)

    entries = (
        JournalEntry.objects.filter(
            tenant_id=line.tenant_id, posted=True,
            date__gte=window_lo, date__lte=window_hi,
            lines__account_id=account_id,
        )
        .exclude(bank_lines__is_reconciled=True)
        .prefetch_related("lines")
        .distinct()
    )

    scored = []
    for entry in entries:
        amount = _entry_amount_for_account(entry, account_id)
        if amount == 0:
            continue
        reasons, score = [], 0
        if amount == Decimal(line.amount):
            score += 60
            reasons.append("amount matches exactly")
        elif abs(amount) == abs(Decimal(line.amount)):
            score += 25
            reasons.append("amount matches but sign differs")
        else:
            continue  # amount must at least agree in magnitude

        ref = (line.bank_reference or "").strip().lower()
        if ref and ref in (entry.reference or "").strip().lower():
            score += 30
            reasons.append("bank reference matches")

        if entry.date == line.date:
            score += 10
            reasons.append("same date")
        else:
            reasons.append(f"{abs((entry.date - line.date).days)} day(s) apart")

        desc = (line.description or "").strip().lower()
        if desc and desc[:12] and desc[:12] in (entry.narration or "").strip().lower():
            score += 5
            reasons.append("narration resembles description")

        scored.append((entry, score, reasons))

    scored.sort(key=lambda x: -x[1])
    return scored


def suggest_matches(statement, *, limit_per_line=3):
    """Ranked suggestions for every unreconciled line on a statement."""
    out = []
    for line in statement.lines.filter(is_reconciled=False):
        cands = candidate_entries(line, account_id=statement.account_id)[:limit_per_line]
        out.append({
            "line": str(line.id),
            "date": str(line.date),
            "description": line.description,
            "amount": str(line.amount),
            "suggestions": [
                {"entry": str(e.id), "reference": e.reference, "narration": e.narration,
                 "date": str(e.date), "score": s, "reasons": r}
                for e, s, r in cands
            ],
        })
    return out


def auto_match(statement, *, actor="", min_score=90):
    """
    Reconcile lines whose best candidate is unambiguous.

    Two guards keep this honest: the match must score at least `min_score`
    (amount + reference, or amount + same date), and it must be strictly better
    than the runner-up. If two entries look equally plausible the line is left
    for a human — silently picking one would hide a duplicate payment.
    """
    matched, ambiguous = [], []
    used_entries: set[str] = set()

    for line in statement.lines.filter(is_reconciled=False):
        cands = candidate_entries(line, account_id=statement.account_id)
        cands = [c for c in cands if str(c[0].id) not in used_entries]
        if not cands:
            continue
        best = cands[0]
        runner_up = cands[1] if len(cands) > 1 else None

        # Tie detection comes BEFORE the score gate on purpose. Two equally
        # plausible candidates is exactly the case a human must see — most often
        # a duplicate payment. Gating on score first would hide it as merely
        # "unmatched", which reads as nothing to look at.
        if runner_up and runner_up[1] == best[1]:
            ambiguous.append({"line": str(line.id), "amount": str(line.amount),
                              "score": best[1],
                              "tied_candidates": [str(best[0].id), str(runner_up[0].id)]})
            continue
        if best[1] < min_score:
            continue

        line.matched_entry = best[0]
        line.is_reconciled = True
        line.reconciled_at = timezone.now()
        line.reconciled_by = actor or "auto-match"
        line.save()
        used_entries.add(str(best[0].id))
        matched.append({"line": str(line.id), "entry": str(best[0].id),
                        "score": best[1], "reasons": best[2]})

    return {
        "matched": len(matched),
        "ambiguous": len(ambiguous),
        "remaining": statement.lines.filter(is_reconciled=False).count(),
        "details": matched,
        "needs_review": ambiguous,
    }


# ── Exception report ─────────────────────────────────────────────────────────
def reconciliation_report(statement):
    """
    The working document: what is still unexplained, in both directions, plus
    whether the period actually reconciles.
    """
    from products.cyed.finance.models import JournalEntry

    unmatched_lines = [
        {"line": str(l.id), "date": str(l.date), "description": l.description, "amount": str(l.amount)}
        for l in statement.lines.filter(is_reconciled=False)
    ]

    # Ledger movement on this account within the period that no bank line claims.
    entries = (
        JournalEntry.objects.filter(
            tenant_id=statement.tenant_id, posted=True,
            date__gte=statement.period_start, date__lte=statement.period_end,
            lines__account_id=statement.account_id,
        )
        .prefetch_related("lines")
        .distinct()
    )
    matched_ids = set(
        str(i) for i in statement.lines.filter(is_reconciled=True)
        .exclude(matched_entry=None).values_list("matched_entry_id", flat=True)
    )
    unmatched_entries = [
        {"entry": str(e.id), "date": str(e.date), "reference": e.reference,
         "narration": e.narration,
         "amount": str(_entry_amount_for_account(e, statement.account_id))}
        for e in entries if str(e.id) not in matched_ids
    ]

    reconciled_total = sum(
        (Decimal(l.amount) for l in statement.lines.filter(is_reconciled=True)), Decimal("0")
    )
    unreconciled_total = sum((Decimal(l["amount"]) for l in unmatched_lines), Decimal("0"))

    return {
        "statement": str(statement.id),
        "period": {"from": str(statement.period_start), "to": str(statement.period_end)},
        "opening_balance": str(statement.opening_balance),
        "declared_closing": str(statement.closing_balance),
        "expected_closing": str(statement.expected_closing),
        "statement_internally_balances": statement.balances,
        "lines_total": statement.lines.count(),
        "lines_reconciled": statement.lines.filter(is_reconciled=True).count(),
        "reconciled_value": str(reconciled_total),
        "unreconciled_value": str(unreconciled_total),
        # Money that moved at the bank but was never booked.
        "bank_lines_without_ledger_entry": unmatched_lines,
        # Booked movement the bank never saw — unpresented cheques, duplicates,
        # or something that should not be there at all.
        "ledger_entries_without_bank_line": unmatched_entries,
        "fully_reconciled": statement.is_fully_reconciled and not unmatched_entries,
    }
