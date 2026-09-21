"""Financial statement endpoints — trial balance, P&L, balance sheet."""

from datetime import date

from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import IsAuthenticatedViaClaims
from products.cycom.accounting.bank_reconciliation import reconciliation_summary
from products.cycom.accounting.models import Budget
from products.cycom.accounting.reports import (
    balance_sheet,
    budget_vs_actual,
    cash_flow_statement,
    profit_and_loss,
    trial_balance,
    vat_return,
)


def _date(qp, key):
    v = qp.get(key)
    if not v:
        return None
    try:
        return date.fromisoformat(v)
    except ValueError:
        return None


class TrialBalanceView(APIView):
    permission_classes = [IsAuthenticatedViaClaims]

    def get(self, request):
        return Response(trial_balance(request.tenant_id, date_to=_date(request.query_params, "date_to")))


class ProfitAndLossView(APIView):
    permission_classes = [IsAuthenticatedViaClaims]

    def get(self, request):
        return Response(profit_and_loss(
            request.tenant_id,
            date_from=_date(request.query_params, "date_from"),
            date_to=_date(request.query_params, "date_to"),
        ))


class BalanceSheetView(APIView):
    permission_classes = [IsAuthenticatedViaClaims]

    def get(self, request):
        return Response(balance_sheet(request.tenant_id, date_to=_date(request.query_params, "date_to")))


class VatReturnView(APIView):
    permission_classes = [IsAuthenticatedViaClaims]

    def get(self, request):
        return Response(vat_return(
            request.tenant_id,
            date_from=_date(request.query_params, "date_from"),
            date_to=_date(request.query_params, "date_to"),
        ))


class CashFlowStatementView(APIView):
    permission_classes = [IsAuthenticatedViaClaims]

    def get(self, request):
        return Response(cash_flow_statement(
            request.tenant_id,
            date_from=_date(request.query_params, "date_from"),
            date_to=_date(request.query_params, "date_to"),
        ))


class BudgetVsActualView(APIView):
    permission_classes = [IsAuthenticatedViaClaims]

    def get(self, request, pk):
        try:
            budget = Budget.objects.get(pk=pk, tenant_id=request.tenant_id)
        except Budget.DoesNotExist:
            return Response({"detail": "Not found."}, status=404)
        return Response(budget_vs_actual(budget))


class BankReconciliationSummaryView(APIView):
    permission_classes = [IsAuthenticatedViaClaims]

    def get(self, request):
        bank_account_id = request.query_params.get("bank_account")
        if not bank_account_id:
            return Response({"detail": "bank_account is required."}, status=400)
        ending_balance = request.query_params.get("statement_ending_balance")
        return Response(reconciliation_summary(
            request.tenant_id,
            bank_account_id=bank_account_id,
            date_to=_date(request.query_params, "date_to"),
            statement_ending_balance=ending_balance,
        ))
