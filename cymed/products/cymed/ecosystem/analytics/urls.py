"""URL routes for the CyMed ecosystem analytics sub-app."""
from __future__ import annotations

from django.urls import path

from .views import (
    AnalyticsExportViewSet,
    AnalyticsSnapshotViewSet,
    DashboardViewSet,
    DashboardWidgetViewSet,
)


urlpatterns = [
    path(
        "snapshots/",
        AnalyticsSnapshotViewSet.as_view({"get": "list"}),
        name="analytics-snapshot-list",
    ),
    path(
        "snapshots/<uuid:pk>/",
        AnalyticsSnapshotViewSet.as_view({"get": "retrieve"}),
        name="analytics-snapshot-detail",
    ),
    path(
        "snapshots/snapshot-patient-flow/",
        AnalyticsSnapshotViewSet.as_view({"post": "snapshot_patient_flow"}),
        name="analytics-snapshot-patient-flow",
    ),
    path(
        "snapshots/snapshot-revenue/",
        AnalyticsSnapshotViewSet.as_view({"post": "snapshot_revenue"}),
        name="analytics-snapshot-revenue",
    ),
    path(
        "snapshots/snapshot-referral-network/",
        AnalyticsSnapshotViewSet.as_view({"post": "snapshot_referral_network"}),
        name="analytics-snapshot-referral-network",
    ),
    path(
        "snapshots/snapshot-provider-utilisation/",
        AnalyticsSnapshotViewSet.as_view({"post": "snapshot_provider_utilisation"}),
        name="analytics-snapshot-provider-utilisation",
    ),
    path(
        "dashboards/",
        DashboardViewSet.as_view({"get": "list", "post": "create"}),
        name="analytics-dashboard-list",
    ),
    path(
        "dashboards/<uuid:pk>/",
        DashboardViewSet.as_view(
            {
                "get": "retrieve",
                "put": "update",
                "patch": "partial_update",
                "delete": "destroy",
            }
        ),
        name="analytics-dashboard-detail",
    ),
    path(
        "dashboards/create/",
        DashboardViewSet.as_view({"post": "create_dashboard"}),
        name="analytics-dashboard-create",
    ),
    path(
        "dashboards/<uuid:pk>/add-widget/",
        DashboardViewSet.as_view({"post": "add_widget"}),
        name="analytics-dashboard-add-widget",
    ),
    path(
        "widgets/",
        DashboardWidgetViewSet.as_view({"get": "list", "post": "create"}),
        name="analytics-widget-list",
    ),
    path(
        "widgets/<uuid:pk>/",
        DashboardWidgetViewSet.as_view(
            {
                "get": "retrieve",
                "put": "update",
                "patch": "partial_update",
                "delete": "destroy",
            }
        ),
        name="analytics-widget-detail",
    ),
    path(
        "exports/",
        AnalyticsExportViewSet.as_view({"get": "list", "post": "create"}),
        name="analytics-export-list",
    ),
    path(
        "exports/<uuid:pk>/",
        AnalyticsExportViewSet.as_view(
            {
                "get": "retrieve",
                "put": "update",
                "patch": "partial_update",
                "delete": "destroy",
            }
        ),
        name="analytics-export-detail",
    ),
    path(
        "exports/queue/",
        AnalyticsExportViewSet.as_view({"post": "queue_export"}),
        name="analytics-export-queue",
    ),
    path(
        "exports/<uuid:pk>/complete/",
        AnalyticsExportViewSet.as_view({"post": "complete_export"}),
        name="analytics-export-complete",
    ),
    path(
        "exports/<uuid:pk>/fail/",
        AnalyticsExportViewSet.as_view({"post": "fail_export"}),
        name="analytics-export-fail",
    ),
]
