"""General-ledger services: balanced posting + trial balance."""

from decimal import ROUND_HALF_UP, Decimal

from django.db.models import DecimalField, F, Q, Sum, Value
from django.db.models.functions import Coalesce

from products.cyed.finance.models import Account, JournalEntry, JournalLine

CENT = Decimal("0.01")


def _q(x):
    """Round to cents, half-up — the convention Australian money uses."""
    return Decimal(x).quantize(CENT, rounding=ROUND_HALF_UP)


class UnbalancedEntry(Exception):
    pass


def post_entry(*, tenant_id, date, reference, narration, lines):
    """
    lines = [{account_id, debit, credit, description}]. Enforces double-entry
    (debits == credits > 0) before posting.
    """
    total_debit = sum((Decimal(str(l.get("debit", 0))) for l in lines), Decimal("0"))
    total_credit = sum((Decimal(str(l.get("credit", 0))) for l in lines), Decimal("0"))
    if total_debit != total_credit or total_debit <= 0:
        raise UnbalancedEntry(f"Entry not balanced: debits {total_debit} != credits {total_credit}")

    entry = JournalEntry.objects.create(
        tenant_id=tenant_id, date=date, reference=reference, narration=narration, posted=True,
    )
    for l in lines:
        JournalLine.objects.create(
            tenant_id=tenant_id, entry=entry, account_id=l["account_id"],
            debit=Decimal(str(l.get("debit", 0))), credit=Decimal(str(l.get("credit", 0))),
            description=l.get("description", ""),
        )
    return entry


def _movements(tenant_id, account_types, date_from=None, date_to=None):
    """
    Net movement per account for the given types over an optional period.

    Aggregated in SQL. The previous version ran one query per account and then
    summed the rows in Python, so a year of postings pulled every journal line
    into memory to produce a handful of totals — the report degraded in
    proportion to how long the school had been using the system, which is the
    worst possible shape for a month-end report.
    """
    rows = []
    for acc in (
        Account.objects.filter(tenant_id=tenant_id, account_type__in=account_types)
        .annotate(
            dr=Coalesce(
                Sum("lines__debit", filter=_line_filter(date_from, date_to)),
                Value(Decimal("0")), output_field=DecimalField(max_digits=18, decimal_places=2),
            ),
            cr=Coalesce(
                Sum("lines__credit", filter=_line_filter(date_from, date_to)),
                Value(Decimal("0")), output_field=DecimalField(max_digits=18, decimal_places=2),
            ),
        )
        .order_by("code")
    ):
        if not acc.dr and not acc.cr:
            continue
        # Natural balance: debit for asset/expense, credit for income/liability/equity.
        balance = acc.dr - acc.cr if acc.account_type in ("asset", "expense") else acc.cr - acc.dr
        rows.append({"code": acc.code, "name": acc.name, "type": acc.account_type,
                     "amount": _q(balance)})
    return rows


def _line_filter(date_from=None, date_to=None):
    """The posted-and-in-period condition, shared by the debit and credit sums."""
    condition = Q(lines__entry__posted=True)
    if date_from:
        condition &= Q(lines__entry__date__gte=date_from)
    if date_to:
        condition &= Q(lines__entry__date__lte=date_to)
    return condition


def profit_and_loss(tenant_id, date_from=None, date_to=None):
    """Income statement: income less expenses for the period."""
    income = _movements(tenant_id, ["income"], date_from, date_to)
    expense = _movements(tenant_id, ["expense"], date_from, date_to)
    total_income = sum((r["amount"] for r in income), Decimal("0"))
    total_expense = sum((r["amount"] for r in expense), Decimal("0"))
    net = total_income - total_expense
    return {
        "report": "profit_and_loss",
        "period": {"from": str(date_from or ""), "to": str(date_to or "")},
        "income": [{**r, "amount": str(r["amount"])} for r in income],
        "expenses": [{**r, "amount": str(r["amount"])} for r in expense],
        "total_income": str(total_income),
        "total_expenses": str(total_expense),
        "net_surplus": str(net),  # schools run a surplus/deficit, not a "profit"
    }


def balance_sheet(tenant_id, as_of=None):
    """
    Statement of financial position as at a date. Retained surplus is derived
    from income less expenses so the sheet balances without a closing entry.
    """
    assets = _movements(tenant_id, ["asset"], None, as_of)
    liabilities = _movements(tenant_id, ["liability"], None, as_of)
    equity = _movements(tenant_id, ["equity"], None, as_of)

    pl = profit_and_loss(tenant_id, None, as_of)
    retained = Decimal(pl["net_surplus"])

    total_assets = sum((r["amount"] for r in assets), Decimal("0"))
    total_liabilities = sum((r["amount"] for r in liabilities), Decimal("0"))
    total_equity = sum((r["amount"] for r in equity), Decimal("0")) + retained

    return {
        "report": "balance_sheet",
        "as_of": str(as_of or ""),
        "assets": [{**r, "amount": str(r["amount"])} for r in assets],
        "liabilities": [{**r, "amount": str(r["amount"])} for r in liabilities],
        "equity": [{**r, "amount": str(r["amount"])} for r in equity],
        "retained_surplus": str(retained),
        "total_assets": str(total_assets),
        "total_liabilities": str(total_liabilities),
        "total_equity": str(total_equity),
        "balanced": total_assets == total_liabilities + total_equity,
    }


def budget_vs_actual(budget):
    """Per-line budget, actual, and variance for a budget cycle."""
    rows = []
    total_budget = total_actual = Decimal("0")
    for line in budget.lines.select_related("account"):
        actual = line.actual()
        rows.append({
            "account_code": line.account.code,
            "account_name": line.account.name,
            "account_type": line.account.account_type,
            "budgeted": str(line.budgeted_amount),
            "actual": str(actual),
            "variance": str(Decimal(line.budgeted_amount) - actual),
            "utilisation_pct": (
                str(round(actual / Decimal(line.budgeted_amount) * 100, 1))
                if Decimal(line.budgeted_amount) else "0"
            ),
        })
        total_budget += Decimal(line.budgeted_amount)
        total_actual += actual
    return {
        "budget": str(budget.id), "name": budget.name, "fiscal_year": budget.fiscal_year,
        "status": budget.status, "rows": rows,
        "total_budgeted": str(total_budget), "total_actual": str(total_actual),
        "total_variance": str(total_budget - total_actual),
    }


# ── GST / BAS (Australian Taxation Office) ───────────────────────────────────
# GST is tracked the way accounting actually tracks it: as ledger accounts, not
# as a field on a document. Two control accounts carry the liability, and the
# BAS is derived from their movement, so the return always agrees with the books.
GST_COLLECTED_CODE = "2200"  # liability: GST charged on sales (BAS label 1A)
GST_PAID_CODE = "1300"       # asset: GST paid on purchases, claimable (label 1B)
GST_RATE = Decimal("0.10")   # 10% in Australia


def gst_accounts(tenant_id):
    """Fetch or create the two GST control accounts."""
    collected, _ = Account.objects.get_or_create(
        tenant_id=tenant_id, code=GST_COLLECTED_CODE,
        defaults={"name": "GST Collected", "account_type": "liability"},
    )
    paid, _ = Account.objects.get_or_create(
        tenant_id=tenant_id, code=GST_PAID_CODE,
        defaults={"name": "GST Paid", "account_type": "asset"},
    )
    return collected, paid


def split_gst(gross_amount, *, inclusive=True, rate=GST_RATE):
    """
    Split an amount into net + GST.

    Australian prices are normally quoted GST-inclusive, so the GST component of
    a $110 sale is $10 (1/11th), not $11. Getting this backwards overstates a
    school's liability, so both directions are supported explicitly.
    """
    gross = Decimal(str(gross_amount))
    if inclusive:
        gst = (gross * rate / (Decimal("1") + rate)).quantize(CENT, rounding=ROUND_HALF_UP)
        return {"net": _q(gross - gst), "gst": gst, "gross": _q(gross)}
    gst = (gross * rate).quantize(CENT, rounding=ROUND_HALF_UP)
    return {"net": _q(gross), "gst": gst, "gross": _q(gross + gst)}


def bas_report(tenant_id, date_from=None, date_to=None):
    """
    Business Activity Statement figures for a period, derived from the ledger.

    Note on scope: most Australian school tuition is GST-FREE under the GST Act,
    while trading activities (uniform shop, canteen, excursions, hire) are
    taxable. This report shows what the ledger holds — it does not decide which
    supplies are taxable. That classification belongs to the school's accountant,
    and pretending otherwise would be dangerous.
    """
    collected, paid = gst_accounts(tenant_id)

    def movement(account):
        lines = account.lines.filter(entry__posted=True)
        if date_from:
            lines = lines.filter(entry__date__gte=date_from)
        if date_to:
            lines = lines.filter(entry__date__lte=date_to)
        dr = sum((l.debit for l in lines), Decimal("0"))
        cr = sum((l.credit for l in lines), Decimal("0"))
        return dr, cr

    _, gst_on_sales = movement(collected)          # credit balance = liability
    gst_on_purchases, _ = movement(paid)           # debit balance = claimable

    income = _movements(tenant_id, ["income"], date_from, date_to)
    expenses = _movements(tenant_id, ["expense"], date_from, date_to)
    total_sales = sum((r["amount"] for r in income), Decimal("0"))
    total_purchases = sum((r["amount"] for r in expenses), Decimal("0"))

    net = _q(gst_on_sales - gst_on_purchases)
    return {
        "report": "bas",
        "period": {"from": str(date_from or ""), "to": str(date_to or "")},
        # ATO BAS labels
        "G1_total_sales": str(_q(total_sales + gst_on_sales)),
        "G11_non_capital_purchases": str(_q(total_purchases + gst_on_purchases)),
        "1A_gst_on_sales": str(_q(gst_on_sales)),
        "1B_gst_on_purchases": str(_q(gst_on_purchases)),
        "net_gst": str(net),
        "position": "payable to ATO" if net > 0 else ("refund from ATO" if net < 0 else "nil"),
        "gst_rate": str(GST_RATE),
        "disclaimer": (
            "Derived from posted ledger movement on the GST control accounts. "
            "GST-free vs taxable classification of each supply is the school's "
            "responsibility; this report does not determine it."
        ),
    }


# ── Debtor aging ─────────────────────────────────────────────────────────────
AGING_BUCKETS = [(0, 30), (31, 60), (61, 90), (91, None)]


def ar_aging(tenant_id, as_of=None):
    """
    Accounts-receivable aging across student invoices and billing installments.

    This is the report a school business manager opens first: who owes what, and
    how long it has been outstanding.
    """
    from datetime import date as _date

    from products.cyed.billing.models import Installment
    from products.cyed.fees.models import Invoice

    today = as_of or _date.today()
    if isinstance(today, str):
        from datetime import datetime

        today = datetime.strptime(today, "%Y-%m-%d").date()

    def bucket_for(days):
        for lo, hi in AGING_BUCKETS:
            if hi is None and days >= lo:
                return f"{lo}+"
            if lo <= days <= hi:
                return f"{lo}-{hi}"
        return "current"

    rows, totals = {}, {f"{lo}-{hi}" if hi else f"{lo}+": Decimal("0") for lo, hi in AGING_BUCKETS}
    totals["not_yet_due"] = Decimal("0")

    def add(student_id, label, due_date, outstanding, kind):
        if outstanding <= 0:
            return
        key = str(student_id)
        r = rows.setdefault(key, {"student": key, "total": Decimal("0"), "items": []})
        if due_date and due_date < today:
            days = (today - due_date).days
            b = bucket_for(days)
        else:
            days, b = 0, "not_yet_due"
        totals[b] = totals.get(b, Decimal("0")) + outstanding
        r["total"] += outstanding
        r["items"].append({"kind": kind, "label": label, "due": str(due_date or ""),
                           "days_overdue": days, "outstanding": str(outstanding), "bucket": b})

    # Outstanding amounts are annotated in SQL rather than read from the
    # `balance` property. The property sums each row's payments in a separate
    # query, so a school with a year of billing paid one query per unpaid
    # invoice *and* per unpaid installment just to build one report.
    money = DecimalField(max_digits=18, decimal_places=2)
    zero = Value(Decimal("0"))

    invoices = (
        Invoice.objects.filter(tenant_id=tenant_id)
        .exclude(status__in=["paid", "cancelled"])
        .annotate(paid=Coalesce(Sum("payments__amount"), zero, output_field=money))
        .annotate(outstanding=F("amount") - F("paid"))
        .values("student_id", "description", "due_date", "outstanding")
    )
    for inv in invoices:
        add(inv["student_id"], inv["description"] or "Invoice", inv["due_date"],
            Decimal(str(inv["outstanding"] or 0)), "invoice")

    installments = (
        Installment.objects.filter(tenant_id=tenant_id)
        .exclude(status="paid")
        .exclude(bill__status="cancelled")
        .annotate(paid=Coalesce(Sum("payments__amount"), zero, output_field=money))
        .annotate(outstanding=F("amount_due") - F("paid"))
        .values("bill__student_id", "installment_no", "due_date", "outstanding")
    )
    for inst in installments:
        add(inst["bill__student_id"], f"Installment {inst['installment_no']}", inst["due_date"],
            Decimal(str(inst["outstanding"] or 0)), "installment")

    return {
        "report": "ar_aging",
        "as_of": str(today),
        "buckets": {k: str(v) for k, v in totals.items()},
        "total_outstanding": str(sum(totals.values(), Decimal("0"))),
        "debtors": sorted(
            ({**r, "total": str(r["total"])} for r in rows.values()),
            key=lambda x: Decimal(x["total"]), reverse=True,
        ),
    }


def trial_balance(tenant_id):
    """
    Sum debits/credits per account across posted entries.

    One grouped query rather than two per account. On a year of data the old
    shape issued 2N queries and materialised every line; this issues one and
    sums in the database.
    """
    rows = []
    total_dr = total_cr = Decimal("0")
    money = DecimalField(max_digits=18, decimal_places=2)
    posted = Q(lines__entry__posted=True)

    for acc in (
        Account.objects.filter(tenant_id=tenant_id)
        .annotate(
            dr=Coalesce(Sum("lines__debit", filter=posted), Value(Decimal("0")), output_field=money),
            cr=Coalesce(Sum("lines__credit", filter=posted), Value(Decimal("0")), output_field=money),
        )
        .order_by("code")
    ):
        if not acc.dr and not acc.cr:
            continue
        # Quantised on the way out: a database SUM returns an unscaled Decimal,
        # so aggregating in SQL would silently change "1000.00" to "1000" on
        # the wire for every consumer of this report.
        rows.append({"code": acc.code, "name": acc.name, "type": acc.account_type,
                     "debit": str(_q(acc.dr)), "credit": str(_q(acc.cr))})
        total_dr += acc.dr
        total_cr += acc.cr
    return {"rows": rows, "total_debit": str(_q(total_dr)), "total_credit": str(_q(total_cr)),
            "balanced": total_dr == total_cr}
