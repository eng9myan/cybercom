from datetime import date

from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from core.viewsets import TenantScopedModelViewSet
from products.cycom.accounting.bank_reconciliation import (
    auto_match,
    import_statement_lines,
    match_line,
    unmatch_line,
)
from products.cycom.accounting.models import (
    Account,
    BankStatementLine,
    Budget,
    FixedAsset,
    JournalEntry,
    JournalLine,
)
from products.cycom.accounting.serializers import (
    AccountSerializer,
    BankStatementLineSerializer,
    BudgetSerializer,
    FixedAssetSerializer,
    JournalEntrySerializer,
    JournalLineSerializer,
)
from products.cycom.accounting.services import run_depreciation


class AccountViewSet(TenantScopedModelViewSet):
    queryset = Account.objects.all()
    serializer_class = AccountSerializer


class JournalEntryViewSet(TenantScopedModelViewSet):
    queryset = JournalEntry.objects.prefetch_related("lines").all()
    serializer_class = JournalEntrySerializer


class JournalLineViewSet(TenantScopedModelViewSet):
    queryset = JournalLine.objects.all()
    serializer_class = JournalLineSerializer


class FixedAssetViewSet(TenantScopedModelViewSet):
    queryset = FixedAsset.objects.select_related(
        "asset_account", "depreciation_expense_account", "accumulated_depreciation_account"
    ).prefetch_related("depreciation_entries").all()
    serializer_class = FixedAssetSerializer
    filterset_fields = ["status"]

    @action(detail=True, methods=["post"])
    def activate(self, request, pk=None):
        asset = self.get_object()
        if asset.status != "draft":
            raise ValidationError(f"Asset is '{asset.status}', can only activate a draft asset.")
        asset.status = "running"
        asset.save(update_fields=["status", "updated_at"])
        return Response(FixedAssetSerializer(asset).data)

    @action(detail=True, methods=["post"], url_path="run-depreciation")
    def run_depreciation_action(self, request, pk=None):
        asset = self.get_object()
        period_str = request.data.get("period")
        period = date.fromisoformat(period_str) if period_str else date.today()
        run_depreciation(asset, period=period)
        asset.refresh_from_db()
        return Response(FixedAssetSerializer(asset).data)

    @action(detail=True, methods=["post"])
    def dispose(self, request, pk=None):
        from django.utils import timezone

        asset = self.get_object()
        if asset.status == "disposed":
            raise ValidationError("Already disposed.")
        asset.status = "disposed"
        asset.disposed_at = timezone.now()
        asset.save(update_fields=["status", "disposed_at", "updated_at"])
        return Response(FixedAssetSerializer(asset).data)


class BudgetViewSet(TenantScopedModelViewSet):
    queryset = Budget.objects.prefetch_related("lines__account").all()
    serializer_class = BudgetSerializer
    filterset_fields = ["fiscal_year", "status"]


class BankStatementLineViewSet(TenantScopedModelViewSet):
    queryset = BankStatementLine.objects.select_related("bank_account", "matched_line").all()
    serializer_class = BankStatementLineSerializer

    @action(detail=False, methods=["post"], url_path="import")
    def import_lines(self, request):
        """Body: {bank_account: <id>, rows: [{statement_date, description, amount, external_ref?}]}"""
        bank_account_id = request.data.get("bank_account")
        rows = request.data.get("rows") or []
        if not bank_account_id or not rows:
            return Response({"detail": "bank_account and rows are required."}, status=400)
        bank_account = Account.objects.get(pk=bank_account_id, tenant_id=request.tenant_id)
        result = import_statement_lines(request.tenant_id, bank_account=bank_account, rows=rows)
        return Response({
            "created": BankStatementLineSerializer(result["created"], many=True).data,
            "skipped_duplicates": result["skipped_duplicates"],
        }, status=201)

    @action(detail=True, methods=["post"], url_path="match")
    def match(self, request, pk=None):
        journal_line_id = request.data.get("journal_line")
        if not journal_line_id:
            return Response({"detail": "journal_line is required."}, status=400)
        line = match_line(request.tenant_id, statement_line_id=pk, journal_line_id=journal_line_id)
        return Response(BankStatementLineSerializer(line).data)

    @action(detail=True, methods=["post"], url_path="unmatch")
    def unmatch(self, request, pk=None):
        line = unmatch_line(request.tenant_id, statement_line_id=pk)
        return Response(BankStatementLineSerializer(line).data)

    @action(detail=False, methods=["post"], url_path="auto-match")
    def auto_match_view(self, request):
        bank_account_id = request.data.get("bank_account")
        if not bank_account_id:
            return Response({"detail": "bank_account is required."}, status=400)
        result = auto_match(request.tenant_id, bank_account_id=bank_account_id)
        return Response(result)
