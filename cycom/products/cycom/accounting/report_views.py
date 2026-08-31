"""Financial statement endpoints — trial balance, P&L, balance sheet."""

from datetime import date

from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import IsAuthenticatedViaClaims
from products.cycom.accounting.reports import (
    balance_sheet,
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
