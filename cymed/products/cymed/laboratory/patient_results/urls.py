"""URL routes for patient results portal APIs."""
from __future__ import annotations

from django.urls import path

from .views import (
    ResultAcknowledgementViewSet,
    ResultDownloadViewSet,
    ResultNotificationViewSet,
    ResultReleaseViewSet,
)

app_name = "cymed_lab_patient_results"

urlpatterns = [
    path(
        "releases/",
        ResultReleaseViewSet.as_view({"get": "list", "post": "create"}),
        name="release-list",
    ),
    path(
        "releases/<uuid:pk>/",
        ResultReleaseViewSet.as_view({
            "get": "retrieve",
            "put": "update",
            "patch": "partial_update",
            "delete": "destroy",
        }),
        name="release-detail",
    ),
    path(
        "releases/release/",
        ResultReleaseViewSet.as_view({"post": "release"}),
        name="release-release",
    ),
    path(
        "releases/<uuid:pk>/retract/",
        ResultReleaseViewSet.as_view({"post": "retract"}),
        name="release-retract",
    ),
    path(
        "releases/<uuid:pk>/notify/",
        ResultReleaseViewSet.as_view({"post": "notify"}),
        name="release-notify",
    ),
    path(
        "releases/<uuid:pk>/acknowledge/",
        ResultReleaseViewSet.as_view({"post": "acknowledge"}),
        name="release-acknowledge",
    ),
    path(
        "releases/<uuid:pk>/download-pdf/",
        ResultReleaseViewSet.as_view({"post": "download_pdf"}),
        name="release-download-pdf",
    ),
    path(
        "downloads/",
        ResultDownloadViewSet.as_view({"get": "list"}),
        name="download-list",
    ),
    path(
        "downloads/<uuid:pk>/",
        ResultDownloadViewSet.as_view({"get": "retrieve"}),
        name="download-detail",
    ),
    path(
        "notifications/",
        ResultNotificationViewSet.as_view({"get": "list"}),
        name="notification-list",
    ),
    path(
        "notifications/<uuid:pk>/",
        ResultNotificationViewSet.as_view({"get": "retrieve"}),
        name="notification-detail",
    ),
    path(
        "acknowledgements/",
        ResultAcknowledgementViewSet.as_view({"get": "list"}),
        name="acknowledgement-list",
    ),
    path(
        "acknowledgements/<uuid:pk>/",
        ResultAcknowledgementViewSet.as_view({"get": "retrieve"}),
        name="acknowledgement-detail",
    ),
]
