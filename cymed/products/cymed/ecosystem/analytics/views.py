"""DRF viewsets for the CyMed ecosystem analytics sub-app."""
from __future__ import annotations

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from . import services
from .models import (
    AnalyticsExport,
    AnalyticsSnapshot,
    Dashboard,
    DashboardWidget,
)
from .serializers import (
    AnalyticsExportSerializer,
    AnalyticsSnapshotSerializer,
    DashboardSerializer,
    DashboardWidgetSerializer,
)


class AnalyticsSnapshotViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AnalyticsSnapshot.objects.all()
    serializer_class = AnalyticsSnapshotSerializer

    @action(detail=False, methods=["post"], url_path="snapshot-patient-flow")
    def snapshot_patient_flow(self, request):
        snapshot = services.snapshot_patient_flow(
            tenant_id=request.data.get("tenant_id"),
            snapshot_date=request.data.get("snapshot_date"),
        )
        return Response(
            AnalyticsSnapshotSerializer(snapshot).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=["post"], url_path="snapshot-revenue")
    def snapshot_revenue(self, request):
        snapshot = services.snapshot_revenue(
            tenant_id=request.data.get("tenant_id"),
            snapshot_date=request.data.get("snapshot_date"),
        )
        return Response(
            AnalyticsSnapshotSerializer(snapshot).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=["post"], url_path="snapshot-referral-network")
    def snapshot_referral_network(self, request):
        snapshot = services.snapshot_referral_network(
            tenant_id=request.data.get("tenant_id"),
            snapshot_date=request.data.get("snapshot_date"),
        )
        return Response(
            AnalyticsSnapshotSerializer(snapshot).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=["post"], url_path="snapshot-provider-utilisation")
    def snapshot_provider_utilisation(self, request):
        snapshot = services.snapshot_provider_utilisation(
            tenant_id=request.data.get("tenant_id"),
            snapshot_date=request.data.get("snapshot_date"),
        )
        return Response(
            AnalyticsSnapshotSerializer(snapshot).data,
            status=status.HTTP_201_CREATED,
        )


class DashboardViewSet(viewsets.ModelViewSet):
    queryset = Dashboard.objects.all()
    serializer_class = DashboardSerializer

    @action(detail=False, methods=["post"], url_path="create")
    def create_dashboard(self, request):
        dashboard = services.create_dashboard(
            tenant_id=request.data.get("tenant_id"),
            code=request.data.get("code"),
            title=request.data.get("title"),
            title_ar=request.data.get("title_ar", ""),
            audience=request.data.get("audience"),
            layout=request.data.get("layout"),
            shared_with_tenant_ids=request.data.get("shared_with_tenant_ids"),
        )
        return Response(
            DashboardSerializer(dashboard).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"], url_path="add-widget")
    def add_widget(self, request, pk=None):
        widget = services.add_widget(
            dashboard_id=pk,
            kind=request.data.get("kind"),
            title=request.data.get("title"),
            data_source=request.data.get("data_source"),
            params=request.data.get("params"),
            position=request.data.get("position", 0),
        )
        return Response(
            DashboardWidgetSerializer(widget).data,
            status=status.HTTP_201_CREATED,
        )


class DashboardWidgetViewSet(viewsets.ModelViewSet):
    queryset = DashboardWidget.objects.all()
    serializer_class = DashboardWidgetSerializer


class AnalyticsExportViewSet(viewsets.ModelViewSet):
    queryset = AnalyticsExport.objects.all()
    serializer_class = AnalyticsExportSerializer

    @action(detail=False, methods=["post"], url_path="queue")
    def queue_export(self, request):
        export = services.queue_export(
            tenant_id=request.data.get("tenant_id"),
            requested_by_profile_id=request.data.get("requested_by_profile_id"),
            kind=request.data.get("kind"),
            filter_payload=request.data.get("filter_payload", {}),
        )
        return Response(
            AnalyticsExportSerializer(export).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"], url_path="complete")
    def complete_export(self, request, pk=None):
        export = services.complete_export(
            export_id=pk,
            file_url=request.data.get("file_url", ""),
        )
        return Response(AnalyticsExportSerializer(export).data)

    @action(detail=True, methods=["post"], url_path="fail")
    def fail_export(self, request, pk=None):
        export = services.fail_export(
            export_id=pk,
            error_message=request.data.get("error_message", ""),
        )
        return Response(AnalyticsExportSerializer(export).data)
