import csv
import io

from django.http import HttpResponse
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError as DrfValidationError
from rest_framework.response import Response

from core.viewsets import TenantScopedModelViewSet
from products.cycom.cyai_reports.models import (
    ReportBuilderSession,
    ReportDefinition,
    ReportSchedule,
    ReportShare,
)
from products.cycom.cyai_reports.query_engine import execute_spec, validate_spec
from products.cycom.cyai_reports.serializers import (
    ReportBuilderSessionSerializer,
    ReportDefinitionSerializer,
    ReportScheduleSerializer,
    ReportShareSerializer,
    SendMessageSerializer,
)
from products.cycom.cyai_reports.services import ReportBuilderAgent


def _as_drf_error(exc):
    return DrfValidationError(str(exc))


class ReportBuilderSessionViewSet(TenantScopedModelViewSet):
    queryset = ReportBuilderSession.objects.all()
    serializer_class = ReportBuilderSessionSerializer

    def perform_create(self, serializer):
        claims = getattr(self.request, "auth_claims", {}) or {}
        serializer.save(tenant_id=self.request.tenant_id, started_by=claims.get("email", ""))

    @action(detail=True, methods=["post"], url_path="message")
    def message(self, request, pk=None):
        session = self.get_object()
        ser = SendMessageSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            result = ReportBuilderAgent.send_message(session, ser.validated_data["content"])
        except Exception as exc:  # noqa: BLE001 — surfaced as a clean 400, not a 500
            raise _as_drf_error(exc)
        return Response(result)

    @action(detail=True, methods=["get"], url_path="preview")
    def preview(self, request, pk=None):
        session = self.get_object()
        try:
            result = ReportBuilderAgent.preview(session)
        except Exception as exc:  # noqa: BLE001
            raise _as_drf_error(exc)
        return Response(result)

    @action(detail=True, methods=["post"], url_path="confirm")
    def confirm(self, request, pk=None):
        """The explicit-confirmation gate — nothing is saved before this call."""
        session = self.get_object()
        try:
            report = ReportBuilderAgent.confirm(session)
        except Exception as exc:  # noqa: BLE001
            raise _as_drf_error(exc)
        return Response(ReportDefinitionSerializer(report).data, status=201)


class ReportDefinitionViewSet(TenantScopedModelViewSet):
    queryset = ReportDefinition.objects.prefetch_related("revisions").all()
    serializer_class = ReportDefinitionSerializer
    http_method_names = ["get", "post", "delete", "head", "options"]  # no raw PUT/PATCH — use revise

    def perform_create(self, serializer):
        # Direct creation (not via builder session) still goes through the
        # same whitelist validation — no free-form spec ever reaches the DB.
        query_spec = self.request.data.get("query_spec")
        try:
            validate_spec(query_spec)
        except Exception as exc:  # noqa: BLE001
            raise _as_drf_error(exc)
        serializer.save(tenant_id=self.request.tenant_id, query_spec=query_spec)

    @action(detail=True, methods=["get"], url_path="run")
    def run(self, request, pk=None):
        """Saved-report execution — never calls the LLM, just replays query_spec."""
        report = self.get_object()
        result = execute_spec(report.query_spec, report.tenant_id)
        return Response(result)

    @action(detail=True, methods=["get"], url_path="export")
    def export(self, request, pk=None):
        report = self.get_object()
        result = execute_spec(report.query_spec, report.tenant_id)

        if result["type"] == "aggregate":
            rows = [{"result": result["result"]}]
        elif result["type"] == "grouped":
            rows = result["rows"]
        else:
            rows = result.get("rows", [])

        output = io.StringIO()
        if rows:
            writer = csv.DictWriter(output, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
        response = HttpResponse(output.getvalue(), content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="{report.name}.csv"'
        return response

    @action(detail=True, methods=["post"], url_path="revise")
    def revise(self, request, pk=None):
        from products.cycom.cyai_reports.models import ReportRevision

        report = self.get_object()
        new_spec = request.data.get("query_spec")
        try:
            validate_spec(new_spec)
        except Exception as exc:  # noqa: BLE001
            raise _as_drf_error(exc)

        report.current_version += 1
        report.query_spec = new_spec
        report.save(update_fields=["query_spec", "current_version"])
        ReportRevision.objects.create(
            tenant_id=report.tenant_id,
            report=report,
            version=report.current_version,
            query_spec=new_spec,
            change_summary=request.data.get("change_summary", ""),
            created_by=(getattr(request, "auth_claims", {}) or {}).get("email", ""),
        )
        return Response(ReportDefinitionSerializer(report).data)

    @action(detail=True, methods=["post"], url_path="share")
    def share(self, request, pk=None):
        report = self.get_object()
        email = request.data.get("email")
        if not email:
            raise DrfValidationError("email is required.")
        share, _ = ReportShare.objects.update_or_create(
            tenant_id=report.tenant_id,
            report=report,
            shared_with_email=email,
            defaults={"can_edit": bool(request.data.get("can_edit", False))},
        )
        report.is_shared = True
        report.save(update_fields=["is_shared"])
        return Response(ReportShareSerializer(share).data, status=201)


class ReportScheduleViewSet(TenantScopedModelViewSet):
    queryset = ReportSchedule.objects.all()
    serializer_class = ReportScheduleSerializer
