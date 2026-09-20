from decimal import Decimal

from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from core.viewsets import TenantScopedModelViewSet
from products.cyed.finance import bankrec, services
from products.cyed.finance.models import (
    Account, BankStatement, BankStatementLine, Budget, BudgetLine, JournalEntry,
)
from products.cyed.finance.serializers import (
    AccountSerializer, BankStatementLineSerializer, BankStatementSerializer,
    BudgetLineSerializer, BudgetSerializer, JournalEntrySerializer,
)
from products.cyed.governance.access import IsFinanceOrLeadership, _email
from products.cyed.security.stepup import RequiresRecentMfa


class AccountViewSet(TenantScopedModelViewSet):
    queryset = Account.objects.all()
    serializer_class = AccountSerializer
    permission_classes = [IsFinanceOrLeadership]


class JournalEntryViewSet(TenantScopedModelViewSet):
    queryset = JournalEntry.objects.prefetch_related("lines").all()
    serializer_class = JournalEntrySerializer
    permission_classes = [IsFinanceOrLeadership]
    http_method_names = ["get", "post", "head", "options"]

    def create(self, request, *args, **kwargs):
        """Post a balanced journal entry. Body: {date, reference, narration, lines:[{account,debit,credit}]}."""
        lines = request.data.get("lines") or []
        norm = [{"account_id": l.get("account"), "debit": l.get("debit", 0),
                 "credit": l.get("credit", 0), "description": l.get("description", "")} for l in lines]
        try:
            entry = services.post_entry(
                tenant_id=request.tenant_id, date=request.data.get("date"),
                reference=request.data.get("reference", ""), narration=request.data.get("narration", ""),
                lines=norm,
            )
        except services.UnbalancedEntry as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(self.get_serializer(entry).data, status=status.HTTP_201_CREATED)


class TrialBalanceView(APIView):
    permission_classes = [IsFinanceOrLeadership]

    def get(self, request):
        return Response(services.trial_balance(request.tenant_id))


class ProfitAndLossView(APIView):
    """GET /api/v1/finance/profit-and-loss/?from=YYYY-MM-DD&to=YYYY-MM-DD"""

    permission_classes = [IsFinanceOrLeadership]

    def get(self, request):
        return Response(services.profit_and_loss(
            request.tenant_id,
            request.query_params.get("from") or None,
            request.query_params.get("to") or None,
        ))


class BalanceSheetView(APIView):
    """GET /api/v1/finance/balance-sheet/?as_of=YYYY-MM-DD"""

    permission_classes = [IsFinanceOrLeadership]

    def get(self, request):
        return Response(services.balance_sheet(
            request.tenant_id, request.query_params.get("as_of") or None
        ))


class BasReportView(APIView):
    """GET /api/v1/finance/bas/?from=&to= — Australian BAS (GST) figures."""

    permission_classes = [IsFinanceOrLeadership]

    def get(self, request):
        return Response(services.bas_report(
            request.tenant_id,
            request.query_params.get("from") or None,
            request.query_params.get("to") or None,
        ))


class ArAgingView(APIView):
    """GET /api/v1/finance/ar-aging/?as_of= — debtor aging across fees + billing."""

    permission_classes = [IsFinanceOrLeadership]

    def get(self, request):
        return Response(services.ar_aging(request.tenant_id, request.query_params.get("as_of") or None))


class BudgetViewSet(TenantScopedModelViewSet):
    queryset = Budget.objects.prefetch_related("lines__account").all()
    serializer_class = BudgetSerializer
    permission_classes = [IsFinanceOrLeadership]

    @action(detail=True, methods=["get"], url_path="vs-actual")
    def vs_actual(self, request, pk=None):
        return Response(services.budget_vs_actual(self.get_object()))

    @action(detail=True, methods=["post"], permission_classes=[IsFinanceOrLeadership, RequiresRecentMfa])
    def approve(self, request, pk=None):
        budget = self.get_object()
        if budget.status != "draft":
            return Response({"detail": f"Budget is already '{budget.status}'."},
                            status=status.HTTP_400_BAD_REQUEST)
        if not budget.lines.exists():
            return Response({"detail": "Add at least one budget line before approving."}, status=400)
        budget.status = "approved"
        budget.approved_by = _email(request)
        budget.save()
        return Response(BudgetSerializer(budget).data)


class BudgetLineViewSet(TenantScopedModelViewSet):
    queryset = BudgetLine.objects.select_related("account", "budget").all()
    serializer_class = BudgetLineSerializer
    permission_classes = [IsFinanceOrLeadership]

    def get_queryset(self):
        qs = super().get_queryset()
        budget = self.request.query_params.get("budget")
        return qs.filter(budget_id=budget) if budget else qs


class BankStatementViewSet(TenantScopedModelViewSet):
    """
    Bank statements and the reconciliation workflow: import a CSV, let the
    matcher do the obvious pairings, then work the exception report.
    """

    queryset = BankStatement.objects.select_related("account").prefetch_related("lines").all()
    serializer_class = BankStatementSerializer
    permission_classes = [IsFinanceOrLeadership]

    def get_queryset(self):
        qs = super().get_queryset()
        params = self.request.query_params
        if params.get("account"):
            qs = qs.filter(account_id=params["account"])
        if params.get("status"):
            qs = qs.filter(status=params["status"])
        return qs

    def perform_create(self, serializer):
        serializer.save(tenant_id=self.request.tenant_id, imported_by=_email(self.request))

    @action(detail=True, methods=["post"], url_path="import")
    def import_lines(self, request, pk=None):
        """POST a bank CSV as multipart field `file`. Re-importing is safe."""
        statement = self.get_object()
        if statement.status == "locked":
            return Response({"detail": "This statement is locked."}, status=status.HTTP_400_BAD_REQUEST)
        upload = request.FILES.get("file")
        if upload is None:
            return Response({"detail": "Attach a CSV as form field 'file'."},
                            status=status.HTTP_400_BAD_REQUEST)
        try:
            report = bankrec.import_statement(statement, upload.read(), filename=upload.name)
        except bankrec.BankImportError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(report)

    @action(detail=True, methods=["get"])
    def suggestions(self, request, pk=None):
        """Ranked candidate ledger entries for each unreconciled line."""
        return Response({"rows": bankrec.suggest_matches(self.get_object())})

    @action(detail=True, methods=["post"], url_path="auto-match")
    def auto_match(self, request, pk=None):
        """
        Reconcile only unambiguous matches. Ties are reported, never guessed —
        picking one of two identical-looking payments would hide a duplicate.
        """
        statement = self.get_object()
        if statement.status == "locked":
            return Response({"detail": "This statement is locked."}, status=400)
        return Response(bankrec.auto_match(statement, actor=_email(request)))

    @action(detail=True, methods=["get"])
    def report(self, request, pk=None):
        """Exception report: unexplained items in both directions."""
        return Response(bankrec.reconciliation_report(self.get_object()))

    @action(detail=True, methods=["post"], permission_classes=[IsFinanceOrLeadership, RequiresRecentMfa])
    def finalise(self, request, pk=None):
        """
        Close the period. Refuses unless every line is matched, nothing on the
        ledger is left unexplained, and the statement's own arithmetic agrees —
        a reconciliation that does not balance is not a reconciliation.
        """
        statement = self.get_object()
        report = bankrec.reconciliation_report(statement)
        problems = []
        if not statement.balances:
            problems.append(
                f"Statement does not add up: opening + lines = {report['expected_closing']}, "
                f"declared closing = {report['declared_closing']}."
            )
        if report["bank_lines_without_ledger_entry"]:
            problems.append(f"{len(report['bank_lines_without_ledger_entry'])} bank line(s) unmatched.")
        if report["ledger_entries_without_bank_line"]:
            problems.append(
                f"{len(report['ledger_entries_without_bank_line'])} ledger entry(ies) the bank never saw."
            )
        if problems:
            return Response({"detail": "Cannot finalise.", "problems": problems, "report": report},
                            status=status.HTTP_400_BAD_REQUEST)

        statement.status = "reconciled"
        statement.reconciled_at = timezone.now()
        statement.save(update_fields=["status", "reconciled_at", "updated_at"])
        return Response({"statement": str(statement.id), "status": statement.status, "report": report})


class BankStatementLineViewSet(TenantScopedModelViewSet):
    """
    Imported bank statement lines and their reconciliation against the ledger.
    """

    queryset = BankStatementLine.objects.select_related("matched_entry").all()
    serializer_class = BankStatementLineSerializer
    permission_classes = [IsFinanceOrLeadership]

    def get_queryset(self):
        qs = super().get_queryset()
        params = self.request.query_params
        if params.get("reconciled") == "0":
            qs = qs.filter(is_reconciled=False)
        elif params.get("reconciled") == "1":
            qs = qs.filter(is_reconciled=True)
        if params.get("from"):
            qs = qs.filter(date__gte=params["from"])
        if params.get("to"):
            qs = qs.filter(date__lte=params["to"])
        return qs

    @action(detail=True, methods=["post"])
    def reconcile(self, request, pk=None):
        """Match this bank line to a posted journal entry."""
        line = self.get_object()
        if line.is_reconciled:
            return Response({"detail": "Line is already reconciled."}, status=400)
        entry_id = request.data.get("entry")
        if not entry_id:
            return Response({"entry": "A journal entry id is required."}, status=400)
        entry = JournalEntry.objects.filter(tenant_id=request.tenant_id, id=entry_id).first()
        if entry is None:
            return Response({"entry": "Unknown journal entry."}, status=400)
        if not entry.posted:
            return Response({"entry": "Only a posted entry can be reconciled against."}, status=400)
        line.matched_entry = entry
        line.is_reconciled = True
        line.reconciled_at = timezone.now()
        line.reconciled_by = _email(request)
        line.save()
        return Response(BankStatementLineSerializer(line).data)

    @action(detail=True, methods=["post"], url_path="unreconcile")
    def unreconcile(self, request, pk=None):
        line = self.get_object()
        line.matched_entry = None
        line.is_reconciled = False
        line.reconciled_at = None
        line.reconciled_by = ""
        line.save()
        return Response(BankStatementLineSerializer(line).data)

    @action(detail=False, methods=["get"], url_path="summary")
    def summary(self, request):
        """Reconciliation status: how much is matched vs outstanding."""
        qs = BankStatementLine.objects.filter(tenant_id=request.tenant_id)
        if request.query_params.get("from"):
            qs = qs.filter(date__gte=request.query_params["from"])
        if request.query_params.get("to"):
            qs = qs.filter(date__lte=request.query_params["to"])
        reconciled = qs.filter(is_reconciled=True)
        outstanding = qs.filter(is_reconciled=False)
        total = sum((Decimal(l.amount) for l in qs), Decimal("0"))
        rec_total = sum((Decimal(l.amount) for l in reconciled), Decimal("0"))
        return Response({
            "lines_total": qs.count(),
            "lines_reconciled": reconciled.count(),
            "lines_outstanding": outstanding.count(),
            "statement_balance": str(total),
            "reconciled_value": str(rec_total),
            "unreconciled_value": str(total - rec_total),
            "fully_reconciled": not outstanding.exists(),
        })
