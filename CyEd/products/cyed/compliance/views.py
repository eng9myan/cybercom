import csv
import io

from rest_framework import status
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet

from core.viewsets import TenantScopedModelViewSet
from products.cyed.compliance import services
from products.cyed.compliance.models import NCCDRecord, StatutoryReportLog
from products.cyed.compliance.serializers import NCCDRecordSerializer, StatutoryReportLogSerializer
from products.cyed.governance.access import (
    ADMIN, LEADERSHIP, IsPastoralOrLeadership, _email, has_any, roles_of,
)


class NCCDRecordViewSet(TenantScopedModelViewSet):
    """Disability adjustment data — pastoral/leadership only (sensitive)."""

    queryset = NCCDRecord.objects.all()
    serializer_class = NCCDRecordSerializer
    permission_classes = [IsPastoralOrLeadership]


class StatutoryReportLogViewSet(ListModelMixin, RetrieveModelMixin, GenericViewSet):
    serializer_class = StatutoryReportLogSerializer
    permission_classes = [IsPastoralOrLeadership]

    def get_queryset(self):
        return StatutoryReportLog.objects.filter(tenant_id=self.request.tenant_id)


class _StatutoryExportView(APIView):
    """
    Base for statutory exports. Leadership/admin only — these feed government
    portals and carry the whole cohort's PII. Supports ?format=csv|json and
    logs every generation for audit.
    """

    report_type = ""

    def get_permissions(self):
        from core.permissions import IsAuthenticatedViaClaims
        return [IsAuthenticatedViaClaims()]

    def build_rows(self, request):  # pragma: no cover - overridden
        raise NotImplementedError

    def period_label(self, request):
        return ""

    def get(self, request):
        if not has_any(request, ADMIN | LEADERSHIP):
            return Response({"detail": "Statutory exports are leadership/office only."},
                            status=status.HTTP_403_FORBIDDEN)
        rows = self.build_rows(request)
        # `format` is reserved by DRF content negotiation, so use `fmt`.
        fmt = request.query_params.get("fmt", "json").lower()

        StatutoryReportLog.objects.create(
            tenant_id=request.tenant_id,
            report_type=self.report_type,
            period=self.period_label(request),
            row_count=len(rows),
            generated_by=_email(request),
            fmt=fmt,
        )

        if fmt == "csv":
            buf = io.StringIO()
            if rows:
                writer = csv.DictWriter(buf, fieldnames=list(rows[0].keys()))
                writer.writeheader()
                writer.writerows(rows)
            resp = Response(buf.getvalue(), content_type="text/csv")
            resp["Content-Disposition"] = f'attachment; filename="{self.report_type}.csv"'
            return resp
        return Response({"report": self.report_type, "period": self.period_label(request),
                         "count": len(rows), "rows": rows})


class NCCDReturnView(_StatutoryExportView):
    report_type = "nccd"

    def period_label(self, request):
        from django.utils import timezone
        return request.query_params.get("year", str(timezone.now().year))

    def build_rows(self, request):
        year = int(self.period_label(request))
        return services.nccd_return(request.tenant_id, year)


class NCCDSummaryView(_StatutoryExportView):
    report_type = "nccd"

    def period_label(self, request):
        from django.utils import timezone
        return request.query_params.get("year", str(timezone.now().year))

    def build_rows(self, request):
        year = int(self.period_label(request))
        return services.nccd_summary(request.tenant_id, year)


class AttendanceReturnView(_StatutoryExportView):
    report_type = "attendance"

    def period_label(self, request):
        f = request.query_params.get("from", "")
        t = request.query_params.get("to", "")
        return f"{f}..{t}"

    def build_rows(self, request):
        return services.attendance_return(
            request.tenant_id,
            request.query_params.get("from") or None,
            request.query_params.get("to") or None,
        )


class NaplanParticipationView(_StatutoryExportView):
    report_type = "naplan"

    def build_rows(self, request):
        return services.naplan_participation(request.tenant_id)


class CensusView(_StatutoryExportView):
    report_type = "census"

    def build_rows(self, request):
        return services.census(request.tenant_id)
