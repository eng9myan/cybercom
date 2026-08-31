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

from decimal import Decimal

from django.db.models import DecimalField, F, Sum

from products.cycom.accounting.models import Account, JournalLine

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
