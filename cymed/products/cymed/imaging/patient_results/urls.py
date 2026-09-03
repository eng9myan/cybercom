"""URL patterns for patient imaging results sub-app."""
from __future__ import annotations

from django.urls import path

from .views import (
    ImageAccessGrantViewSet,
    ReportAcknowledgementViewSet,
    ReportDownloadViewSet,
    ReportReleaseViewSet,
)

urlpatterns = [
    path(
        "report-releases/",
        ReportReleaseViewSet.as_view({"get": "list", "post": "create"}),
        name="report-release-list",
    ),
    path(
        "report-releases/<uuid:pk>/",
        ReportReleaseViewSet.as_view(
            {
                "get": "retrieve",
                "put": "update",
                "patch": "partial_update",
                "delete": "destroy",
            }
        ),
        name="report-release-detail",
    ),
    path(
        "report-releases/release/",
        ReportReleaseViewSet.as_view({"post": "release"}),
        name="report-release-release",
    ),
    path(
        "report-releases/<uuid:pk>/retract/",
        ReportReleaseViewSet.as_view({"post": "retract"}),
        name="report-release-retract",
    ),
    path(
        "report-releases/<uuid:pk>/viewer-link/",
        ReportReleaseViewSet.as_view({"post": "viewer_link"}),
        name="report-release-viewer-link",
    ),
    path(
        "report-releases/<uuid:pk>/record-download/",
        ReportReleaseViewSet.as_view({"post": "record_download"}),
        name="report-release-record-download",
    ),
    path(
        "report-releases/<uuid:pk>/acknowledge/",
        ReportReleaseViewSet.as_view({"post": "acknowledge"}),
        name="report-release-acknowledge",
    ),
    path(
        "report-releases/<uuid:pk>/generate-pdf/",
        ReportReleaseViewSet.as_view({"post": "generate_pdf"}),
        name="report-release-generate-pdf",
    ),
    path(
        "image-access-grants/",
        ImageAccessGrantViewSet.as_view({"get": "list", "post": "create"}),
        name="image-access-grant-list",
    ),
    path(
        "image-access-grants/<uuid:pk>/",
        ImageAccessGrantViewSet.as_view(
            {
                "get": "retrieve",
                "put": "update",
                "patch": "partial_update",
                "delete": "destroy",
            }
        ),
        name="image-access-grant-detail",
    ),
    path(
        "report-downloads/",
        ReportDownloadViewSet.as_view({"get": "list"}),
        name="report-download-list",
    ),
    path(
        "report-downloads/<uuid:pk>/",
        ReportDownloadViewSet.as_view({"get": "retrieve"}),
        name="report-download-detail",
    ),
    path(
        "report-acknowledgements/",
        ReportAcknowledgementViewSet.as_view({"get": "list"}),
        name="report-acknowledgement-list",
    ),
    path(
        "report-acknowledgements/<uuid:pk>/",
        ReportAcknowledgementViewSet.as_view({"get": "retrieve"}),
        name="report-acknowledgement-detail",
    ),
]
