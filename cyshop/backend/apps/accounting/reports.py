"""
Financial statements, computed live from posted journal entries.

    GET /api/v1/accounting/reports/trial-balance/?as_of=YYYY-MM-DD
    GET /api/v1/accounting/reports/income-statement/?date_from=&date_to=
    GET /api/v1/accounting/reports/balance-sheet/?as_of=YYYY-MM-DD
"""
from decimal import Decimal

from django.db.models import Sum
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Account, JournalEntryLine

Z = Decimal("0.00")

# account_type -> "debit" means a positive balance is normally a debit
NORMAL_SIDE = {
    "asset": "debit", "expense": "debit",
    "liability": "credit", "equity": "credit", "revenue": "credit",
}


def _line_qs(tenant_id, *, date_to=None, date_from=None):
    qs = JournalEntryLine.objects.filter(
        tenant_id=tenant_id, is_deleted=False,
        entry__status="posted", entry__is_deleted=False,
    )
    if date_from:
        qs = qs.filter(entry__entry_date__gte=date_from)
    if date_to:
        qs = qs.filter(entry__entry_date__lte=date_to)
    return qs


def _balances(tenant_id, *, date_to=None, date_from=None):
    rows = (
        _line_qs(tenant_id, date_to=date_to, date_from=date_from)
        .values("account_id", "account__code", "account__name", "account__account_type")
        .annotate(debit=Sum("debit"), credit=Sum("credit"))
        .order_by("account__code")
    )
    out = []
    for r in rows:
        debit = r["debit"] or Z
        credit = r["credit"] or Z
        at = r["account__account_type"]
        signed = debit - credit if NORMAL_SIDE.get(at) == "debit" else credit - debit
        out.append({
            "account_id": str(r["account_id"]),
            "code": r["account__code"],
            "name": r["account__name"],
            "account_type": at,
            "debit": debit,
            "credit": credit,
            "balance": signed,
        })
    return out


class TrialBalanceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        as_of = request.query_params.get("as_of")
        rows = _balances(request.tenant_id, date_to=as_of)
        total_debit = sum((r["debit"] for r in rows), Z)
        total_credit = sum((r["credit"] for r in rows), Z)
        return Response({
            "as_of": as_of,
            "rows": rows,
            "total_debit": total_debit,
            "total_credit": total_credit,
            "balanced": total_debit == total_credit,
        })


class IncomeStatementView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        df = request.query_params.get("date_from")
        dt = request.query_params.get("date_to")
        rows = _balances(request.tenant_id, date_from=df, date_to=dt)
        revenue = [r for r in rows if r["account_type"] == "revenue"]
        expense = [r for r in rows if r["account_type"] == "expense"]
        total_rev = sum((r["balance"] for r in revenue), Z)
        total_exp = sum((r["balance"] for r in expense), Z)
        return Response({
            "date_from": df, "date_to": dt,
            "revenue": revenue, "total_revenue": total_rev,
            "expenses": expense, "total_expenses": total_exp,
            "net_income": total_rev - total_exp,
        })


class BalanceSheetView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        as_of = request.query_params.get("as_of")
        rows = _balances(request.tenant_id, date_to=as_of)
        assets = [r for r in rows if r["account_type"] == "asset"]
        liab = [r for r in rows if r["account_type"] == "liability"]
        equity = [r for r in rows if r["account_type"] == "equity"]
        rev = sum((r["balance"] for r in rows if r["account_type"] == "revenue"), Z)
        exp = sum((r["balance"] for r in rows if r["account_type"] == "expense"), Z)
        retained = rev - exp
        total_assets = sum((r["balance"] for r in assets), Z)
        total_liab = sum((r["balance"] for r in liab), Z)
        total_equity = sum((r["balance"] for r in equity), Z) + retained
        return Response({
            "as_of": as_of,
            "assets": assets, "total_assets": total_assets,
            "liabilities": liab, "total_liabilities": total_liab,
            "equity": equity, "retained_earnings": retained,
            "total_equity": total_equity,
            "total_liabilities_and_equity": total_liab + total_equity,
            "balanced": total_assets == total_liab + total_equity,
        })
