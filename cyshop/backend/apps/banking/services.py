"""Statement import, auto-match against the books, and session completion."""
import csv
import io
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation

from django.utils import timezone

from .models import BankStatement, BankStatementLine, ReconciliationSession

Z2 = Decimal("0.01")


def _parse_date(s):
    s = (s or "").strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"unrecognised date '{s}'")


def _num(s):
    s = (s or "").strip().replace(",", "")
    if not s:
        return Decimal("0")
    try:
        return Decimal(s)
    except InvalidOperation:
        return Decimal("0")


def import_statement_csv(bank_account, text, *, reference="", tenant_id=None):
    """CSV columns (case-insensitive, any order):
       date, description, reference, amount   OR   date, description, debit, credit
    """
    reader = csv.DictReader(io.StringIO(text))
    fields = {(f or "").strip().lower(): f for f in (reader.fieldnames or [])}
    if "date" not in fields or "description" not in fields:
        raise ValueError("CSV needs at least 'date' and 'description' columns")

    rows = list(reader)
    stmt = BankStatement.objects.create(
        tenant_id=tenant_id, bank_account=bank_account, reference=reference,
        statement_date=timezone.now().date())
    made = []
    for r in rows:
        g = lambda k: r.get(fields.get(k, ""), "")
        if "amount" in fields:
            amount = _num(g("amount"))
        else:
            amount = _num(g("credit")) - _num(g("debit"))
        line = BankStatementLine.objects.create(
            tenant_id=tenant_id, bank_account=bank_account, statement=stmt,
            txn_date=_parse_date(g("date")), description=g("description")[:255],
            reference=g("reference")[:120], amount=amount.quantize(Z2))
        made.append(line)
    if made:
        stmt.opening_balance = 0
        stmt.closing_balance = sum((l.amount for l in made), Decimal("0")).quantize(Z2)
        stmt.line_count = len(made)
        stmt.statement_date = max(l.txn_date for l in made)
        stmt.save(update_fields=["opening_balance", "closing_balance", "line_count",
                                 "statement_date", "updated_at", "version"])
    return stmt, made


def _book_entries(bank_account, start, end):
    """Candidate book-side transactions to match against — POS payments and
    posted journal lines that hit this account's GL account, within the window."""
    out = []
    try:
        from apps.pos.models import PosPayment
        pays = PosPayment.objects.filter(
            tenant_id=bank_account.tenant_id, is_deleted=False,
            created_at__date__gte=start, created_at__date__lte=end)
        for p in pays:
            out.append({"type": "pos_payment", "id": p.id, "date": p.created_at.date(),
                        "amount": Decimal(p.amount), "label": f"POS {p.method} {p.order_id}"})
    except Exception:
        pass
    if bank_account.gl_account_id:
        try:
            from apps.accounting.models import JournalEntryLine
            jls = JournalEntryLine.objects.filter(
                tenant_id=bank_account.tenant_id, is_deleted=False,
                account_id=bank_account.gl_account_id, entry__status="posted",
                entry__entry_date__gte=start, entry__entry_date__lte=end)
            for jl in jls.select_related("entry"):
                amt = Decimal(jl.debit) - Decimal(jl.credit)
                out.append({"type": "journal_line", "id": jl.id, "date": jl.entry.entry_date,
                            "amount": amt, "label": f"JE {jl.entry.reference}"})
        except Exception:
            pass
    return out


def auto_match(session, *, days=3):
    lines = list(session.bank_account.statement_lines.filter(
        is_deleted=False, matched=False,
        txn_date__gte=session.period_start, txn_date__lte=session.period_end))
    book = _book_entries(session.bank_account, session.period_start, session.period_end)
    used = set()
    matched = 0
    for ln in lines:
        for b in book:
            key = (b["type"], str(b["id"]))
            if key in used:
                continue
            if (b["amount"].quantize(Z2) == ln.amount
                    and abs((b["date"] - ln.txn_date).days) <= days):
                ln.matched = True
                ln.match_type = b["type"]
                ln.match_id = b["id"]
                ln.match_note = b["label"]
                ln.reconciled = True
                ln.save(update_fields=["matched", "match_type", "match_id", "match_note",
                                       "reconciled", "updated_at", "version"])
                used.add(key)
                matched += 1
                break
    _refresh(session)
    return matched


def _refresh(session):
    ba = session.bank_account
    session.book_balance = ba.book_balance
    session.statement_closing_balance = session.statement_closing_balance or Decimal("0")
    session.difference = (session.statement_closing_balance - session.book_balance).quantize(Z2)
    session.save(update_fields=["book_balance", "difference", "updated_at", "version"])


def complete(session):
    _refresh(session)
    session.status = "completed"
    session.completed_at = timezone.now()
    session.save(update_fields=["status", "completed_at", "updated_at", "version"])
    return session
