from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from . import services
from .models import (
    BankAccount, BankStatement, BankStatementLine, ReconciliationSession,
)
from .serializers import (
    BankAccountSerializer, BankStatementLineSerializer, BankStatementSerializer,
    ReconciliationSessionSerializer,
)


class _T:
    permission_classes = [IsAuthenticated]

    def _tid(self):
        return self.request.tenant_id


class BankAccountViewSet(_T, viewsets.ModelViewSet):
    serializer_class = BankAccountSerializer

    def get_queryset(self):
        return BankAccount.objects.filter(tenant_id=self._tid(), is_deleted=False)

    @action(detail=True, methods=["post"], url_path="import-statement")
    def import_statement(self, request, pk=None):
        acc = self.get_object()
        csv_text = request.data.get("csv") or ""
        if not csv_text:
            return Response({"detail": "Provide a 'csv' string."}, status=400)
        try:
            stmt, lines = services.import_statement_csv(
                acc, csv_text, reference=request.data.get("reference", ""), tenant_id=self._tid())
        except ValueError as e:
            return Response({"detail": str(e)}, status=400)
        return Response({
            "statement": BankStatementSerializer(stmt).data,
            "imported_lines": len(lines),
        }, status=201)


class BankStatementLineViewSet(_T, viewsets.ModelViewSet):
    serializer_class = BankStatementLineSerializer
    http_method_names = ["get", "patch", "head", "options"]

    def get_queryset(self):
        qs = BankStatementLine.objects.filter(tenant_id=self._tid(), is_deleted=False)
        for f in ("bank_account", "statement", "matched", "reconciled"):
            v = self.request.query_params.get(f)
            if v is not None:
                if f in ("matched", "reconciled"):
                    v = v.lower() in ("1", "true", "yes")
                qs = qs.filter(**{f: v})
        return qs

    @action(detail=True, methods=["post"])
    def match(self, request, pk=None):
        ln = self.get_object()
        ln.matched = True
        ln.reconciled = True
        ln.match_type = request.data.get("match_type", "manual")
        ln.match_note = request.data.get("note", "")[:255]
        mid = request.data.get("match_id")
        ln.match_id = mid or None
        ln.save()
        return Response(BankStatementLineSerializer(ln).data)

    @action(detail=True, methods=["post"])
    def unmatch(self, request, pk=None):
        ln = self.get_object()
        ln.matched = ln.reconciled = False
        ln.match_type = ln.match_note = ""
        ln.match_id = None
        ln.save()
        return Response(BankStatementLineSerializer(ln).data)


class ReconciliationSessionViewSet(_T, viewsets.ModelViewSet):
    serializer_class = ReconciliationSessionSerializer

    def get_queryset(self):
        qs = ReconciliationSession.objects.filter(tenant_id=self._tid(), is_deleted=False)
        ba = self.request.query_params.get("bank_account")
        if ba:
            qs = qs.filter(bank_account=ba)
        return qs

    @action(detail=True, methods=["post"], url_path="auto-match")
    def auto_match(self, request, pk=None):
        s = self.get_object()
        n = services.auto_match(s, days=int(request.data.get("days", 3)))
        return Response({"matched": n,
                         "session": ReconciliationSessionSerializer(s).data})

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        s = services.complete(self.get_object())
        return Response(ReconciliationSessionSerializer(s).data)
