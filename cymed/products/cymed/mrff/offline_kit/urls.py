"""URL routes for CyMed MRFF offline_kit sub-app."""
from __future__ import annotations

from django.urls import path

from .views import (
    ConflictResolutionViewSet,
    OfflineCdssRunViewSet,
    OfflineDeviceViewSet,
    OfflineIntakeViewSet,
    SyncQueueItemViewSet,
)


urlpatterns = [
    path(
        "devices/",
        OfflineDeviceViewSet.as_view({"get": "list", "post": "create"}),
        name="offline-device-list",
    ),
    path(
        "devices/<uuid:pk>/",
        OfflineDeviceViewSet.as_view(
            {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
        ),
        name="offline-device-detail",
    ),
    path(
        "devices/register/",
        OfflineDeviceViewSet.as_view({"post": "register"}),
        name="offline-device-register",
    ),
    path(
        "devices/<uuid:pk>/sync-next-batch/",
        OfflineDeviceViewSet.as_view({"post": "sync_next_batch"}),
        name="offline-device-sync-next-batch",
    ),
    path(
        "intakes/",
        OfflineIntakeViewSet.as_view({"get": "list", "post": "create"}),
        name="offline-intake-list",
    ),
    path(
        "intakes/<uuid:pk>/",
        OfflineIntakeViewSet.as_view(
            {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
        ),
        name="offline-intake-detail",
    ),
    path(
        "intakes/capture/",
        OfflineIntakeViewSet.as_view({"post": "capture"}),
        name="offline-intake-capture",
    ),
    path(
        "intakes/<uuid:pk>/record-cdss/",
        OfflineIntakeViewSet.as_view({"post": "record_cdss"}),
        name="offline-intake-record-cdss",
    ),
    path(
        "sync-queue/",
        SyncQueueItemViewSet.as_view({"get": "list", "post": "create"}),
        name="sync-queue-list",
    ),
    path(
        "sync-queue/<uuid:pk>/",
        SyncQueueItemViewSet.as_view(
            {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
        ),
        name="sync-queue-detail",
    ),
    path(
        "sync-queue/enqueue/",
        SyncQueueItemViewSet.as_view({"post": "enqueue"}),
        name="sync-queue-enqueue",
    ),
    path(
        "conflicts/",
        ConflictResolutionViewSet.as_view({"get": "list", "post": "create"}),
        name="conflict-resolution-list",
    ),
    path(
        "conflicts/<uuid:pk>/",
        ConflictResolutionViewSet.as_view(
            {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
        ),
        name="conflict-resolution-detail",
    ),
    path(
        "conflicts/<uuid:pk>/resolve/",
        ConflictResolutionViewSet.as_view({"post": "resolve"}),
        name="conflict-resolution-resolve",
    ),
    path(
        "cdss-runs/",
        OfflineCdssRunViewSet.as_view({"get": "list"}),
        name="offline-cdss-run-list",
    ),
    path(
        "cdss-runs/<uuid:pk>/",
        OfflineCdssRunViewSet.as_view({"get": "retrieve"}),
        name="offline-cdss-run-detail",
    ),
]
