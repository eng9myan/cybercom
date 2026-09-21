"""
Financial statements from the posted general ledger.

Only status='posted' journal lines count — drafts never hit the reports.
Sign convention:
  * asset, expense  -> normal debit balance  = debit - credit
  * liability, equity, income -> normal credit balance = credit - debit

All three statements tie out:
  Trial balance: total debits == total credits.
  P&L: net_profit = income - expenses.
  Balance sheet: assets == liabilities + equity + net_profit(period).
"""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from django.db.models import DecimalField, F, Sum

from products.cycom.accounting.models import Account, JournalEntry, JournalLine

# Reports are stated in the tenant's base/reporting currency. Each journal line
# carries `exchange_rate` = base-currency units per unit of the line currency
# (1 for base-currency lines), so amounts are converted as amount * exchange_rate
# before aggregation. A well-formed multi-currency entry balances in the base
# currency; an entry that only balanced in its transaction currency will
# (correctly) surface as an imbalance.
_CONVERTED = DecimalField(max_digits=20, decimal_places=6)

DEBIT_NORMAL = {"asset", "expense"}
Z = Decimal("0.00")


def _q(x) -> Decimal:
    return (x or Z).quantize(Decimal("0.01"))


def _account_balances(tenant_id, *, date_from=None, date_to=None):
    """Return {account_id: {code,name,type,debit,credit}} over posted lines."""
    lines = JournalLine.objects.filter(tenant_id=tenant_id, entry__status="posted")
    if date_from:
        lines = lines.filter(entry__date__gte=date_from)
    if date_to:
        lines = lines.filter(entry__date__lte=date_to)

    agg = lines.values("account").annotate(
        d=Sum(F("debit") * F("exchange_rate"), output_field=_CONVERTED),
        c=Sum(F("credit") * F("exchange_rate"), output_field=_CONVERTED),
    )
    by_id = {r["account"]: (r["d"] or Z, r["c"] or Z) for r in agg}

    accounts = {a.id: a for a in Account.objects.filter(tenant_id=tenant_id)}
    out = {}
    for aid, acc in accounts.items():
        d, c = by_id.get(aid, (Z, Z))
        out[aid] = {"code": acc.code, "name": acc.name, "type": acc.account_type, "debit": d, "credit": c}
    return out


def _signed_balance(row) -> Decimal:
    net = row["debit"] - row["credit"]
    return net if row["type"] in DEBIT_NORMAL else -net


def trial_balance(tenant_id, *, date_to=None):
    rows = _account_balances(tenant_id, date_to=date_to)
    lines, td, tc = [], Z, Z
    for r in sorted(rows.values(), key=lambda x: x["code"]):
        d, c = r["debit"], r["credit"]
        if d == Z and c == Z:
            continue
        # Present each account's net on its normal side.
        net = d - c
        dbal = net if net > 0 else Z
        cbal = -net if net < 0 else Z
        td += dbal
        tc += cbal
        lines.append({"code": r["code"], "name": r["name"], "type": r["type"],
                      "debit": _q(dbal), "credit": _q(cbal)})
    return {
        "lines": lines,
        "total_debit": _q(td),
        "total_credit": _q(tc),
        "balanced": _q(td) == _q(tc),
    }


def profit_and_loss(tenant_id, *, date_from=None, date_to=None):
    rows = _account_balances(tenant_id, date_from=date_from, date_to=date_to)
    income, expense = [], []
    inc_total = exp_total = Z
    for r in sorted(rows.values(), key=lambda x: x["code"]):
        bal = _signed_balance(r)
        if r["type"] == "income" and bal != Z:
            inc_total += bal
            income.append({"code": r["code"], "name": r["name"], "amount": _q(bal)})
        elif r["type"] == "expense" and bal != Z:
            exp_total += bal
            expense.append({"code": r["code"], "name": r["name"], "amount": _q(bal)})
    return {
        "income": income,
        "expenses": expense,
        "total_income": _q(inc_total),
        "total_expenses": _q(exp_total),
        "net_profit": _q(inc_total - exp_total),
        "period": {"from": str(date_from) if date_from else None, "to": str(date_to) if date_to else None},
    }


def vat_return(tenant_id, *, date_from=None, date_to=None,
               output_code="2120", input_code="1150"):
    """
    VAT/GST return for a period.
      output_tax = tax collected on sales   (Sales Tax Payable, credit-normal)
      input_tax  = tax paid on purchases    (Sales Tax Receivable, debit-normal)
      net_payable = output_tax - input_tax  (positive = owed to authority)
    """
    rows = _account_balances(tenant_id, date_from=date_from, date_to=date_to)
    out_tax = inp_tax = Z
    for r in rows.values():
        if r["code"] == output_code:
            out_tax = r["credit"] - r["debit"]
        elif r["code"] == input_code:
            inp_tax = r["debit"] - r["credit"]
    return {
        "output_tax": _q(out_tax),
        "input_tax": _q(inp_tax),
        "net_payable": _q(out_tax - inp_tax),
        "period": {"from": str(date_from) if date_from else None, "to": str(date_to) if date_to else None},
    }


def balance_sheet(tenant_id, *, date_to=None):
    rows = _account_balances(tenant_id, date_to=date_to)
    assets, liabilities, equity = [], [], []
    a_total = l_total = e_total = Z
    inc_total = exp_total = Z
    for r in sorted(rows.values(), key=lambda x: x["code"]):
        bal = _signed_balance(r)
        if bal == Z:
            continue
        if r["type"] == "asset":
            a_total += bal
            assets.append({"code": r["code"], "name": r["name"], "amount": _q(bal)})
        elif r["type"] == "liability":
            l_total += bal
            liabilities.append({"code": r["code"], "name": r["name"], "amount": _q(bal)})
        elif r["type"] == "equity":
            e_total += bal
            equity.append({"code": r["code"], "name": r["name"], "amount": _q(bal)})
        elif r["type"] == "income":
            inc_total += bal
        elif r["type"] == "expense":
            exp_total += bal
    net_profit = inc_total - exp_total
    equity_with_earnings = e_total + net_profit
    return {
        "assets": assets,
        "liabilities": liabilities,
        "equity": equity,
        "total_assets": _q(a_total),
        "total_liabilities": _q(l_total),
        "total_equity": _q(e_total),
        "current_period_earnings": _q(net_profit),
        "total_equity_and_earnings": _q(equity_with_earnings),
        "total_liabilities_and_equity": _q(l_total + equity_with_earnings),
        "balanced": _q(a_total) == _q(l_total + equity_with_earnings),
    }


def cash_flow_statement(tenant_id, *, date_from=None, date_to=None):
    """
    Direct-method statement of cash flows. Accounts tagged
    cash_flow_type='cash' are the accounts being reconciled; every posted
    entry that touches one is classified by its OTHER lines' cash_flow_type
    (operating/investing/financing). An entry whose counter-accounts are
    unclassified or mixed lands in 'uncategorized' rather than being guessed
    at — tag your accounts to get a real breakdown.
    """
    cash_account_ids = set(
        Account.objects.filter(tenant_id=tenant_id, cash_flow_type="cash").values_list("id", flat=True)
    )
    if not cash_account_ids:
        return {
            "opening_balance": Z, "operating_activities": Z, "investing_activities": Z,
            "financing_activities": Z, "uncategorized": Z, "net_change": Z, "closing_balance": Z,
            "warning": "No accounts tagged cash_flow_type='cash' — nothing to report.",
            "period": {"from": str(date_from) if date_from else None, "to": str(date_to) if date_to else None},
        }

    account_category = dict(
        Account.objects.filter(tenant_id=tenant_id).values_list("id", "cash_flow_type")
    )

    opening = Z
    if date_from:
        opening_rows = _account_balances(tenant_id, date_to=date_from - timedelta(days=1))
        opening = sum(
            _signed_balance(r) for aid, r in opening_rows.items() if aid in cash_account_ids
        )

    totals = {"operating": Z, "investing": Z, "financing": Z, "uncategorized": Z}

    entries = JournalEntry.objects.filter(
        tenant_id=tenant_id, status="posted", lines__account_id__in=cash_account_ids
    ).distinct()
    if date_from:
        entries = entries.filter(date__gte=date_from)
    if date_to:
        entries = entries.filter(date__lte=date_to)

    for entry in entries.prefetch_related("lines"):
        lines = list(entry.lines.all())
        cash_net = sum(
            (l.debit - l.credit) * l.exchange_rate for l in lines if l.account_id in cash_account_ids
        )
        if cash_net == 0:
            continue
        other_categories = {
            account_category.get(l.account_id) for l in lines if l.account_id not in cash_account_ids
        } - {None, "", "cash"}
        category = other_categories.pop() if len(other_categories) == 1 else "uncategorized"
        totals[category] += cash_net

    net_change = totals["operating"] + totals["investing"] + totals["financing"] + totals["uncategorized"]
    return {
        "opening_balance": _q(opening),
        "operating_activities": _q(totals["operating"]),
        "investing_activities": _q(totals["investing"]),
        "financing_activities": _q(totals["financing"]),
        "uncategorized": _q(totals["uncategorized"]),
        "net_change": _q(net_change),
        "closing_balance": _q(opening + net_change),
        "period": {"from": str(date_from) if date_from else None, "to": str(date_to) if date_to else None},
    }


def budget_vs_actual(budget):
    """budget: a Budget instance. Reuses the same account-balance engine as
    every other statement so 'actual' always ties to the GL."""
    balances = _account_balances(budget.tenant_id, date_from=budget.date_from, date_to=budget.date_to)
    lines = []
    total_planned = total_actual = Z
    for bl in budget.lines.select_related("account").all():
        row = balances.get(bl.account_id) or {
            "code": bl.account.code, "name": bl.account.name,
            "type": bl.account.account_type, "debit": Z, "credit": Z,
        }
        actual = _signed_balance(row)
        total_planned += bl.planned_amount
        total_actual += actual
        lines.append({
            "account_code": row["code"],
            "account_name": row["name"],
            "planned": _q(bl.planned_amount),
            "actual": _q(actual),
            "variance": _q(actual - bl.planned_amount),
        })
    return {
        "budget": budget.name,
        "fiscal_year": budget.fiscal_year,
        "lines": lines,
        "total_planned": _q(total_planned),
        "total_actual": _q(total_actual),
        "total_variance": _q(total_actual - total_planned),
        "period": {"from": str(budget.date_from), "to": str(budget.date_to)},
    }
