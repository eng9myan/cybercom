"""CyMed Pharmacy robotics URL routes."""
from django.urls import path

from .views import (
    DispenseJobViewSet,
    RobotBinInventoryViewSet,
    RobotDeviceViewSet,
    RobotEventViewSet,
)

urlpatterns = [
    path(
        "devices/",
        RobotDeviceViewSet.as_view({"get": "list", "post": "create"}),
        name="robotics-device-list",
    ),
    path(
        "devices/<uuid:pk>/",
        RobotDeviceViewSet.as_view(
            {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
        ),
        name="robotics-device-detail",
    ),
    path(
        "devices/<uuid:pk>/heartbeat/",
        RobotDeviceViewSet.as_view({"post": "heartbeat"}),
        name="robotics-device-heartbeat",
    ),
    path(
        "devices/<uuid:pk>/dispatch-dispense/",
        RobotDeviceViewSet.as_view({"post": "dispatch_dispense"}),
        name="robotics-device-dispatch-dispense",
    ),
    path(
        "devices/<uuid:pk>/restock/",
        RobotDeviceViewSet.as_view({"post": "restock"}),
        name="robotics-device-restock",
    ),
    path(
        "devices/<uuid:pk>/lookup-bin/",
        RobotDeviceViewSet.as_view({"get": "lookup_bin"}),
        name="robotics-device-lookup-bin",
    ),
    path(
        "bins/",
        RobotBinInventoryViewSet.as_view({"get": "list", "post": "create"}),
        name="robotics-bin-list",
    ),
    path(
        "bins/<uuid:pk>/",
        RobotBinInventoryViewSet.as_view(
            {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
        ),
        name="robotics-bin-detail",
    ),
    path(
        "jobs/",
        DispenseJobViewSet.as_view({"get": "list", "post": "create"}),
        name="robotics-job-list",
    ),
    path(
        "jobs/<uuid:pk>/",
        DispenseJobViewSet.as_view(
            {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
        ),
        name="robotics-job-detail",
    ),
    path(
        "jobs/<uuid:pk>/mark-completed/",
        DispenseJobViewSet.as_view({"post": "mark_completed"}),
        name="robotics-job-mark-completed",
    ),
    path(
        "jobs/<uuid:pk>/mark-failed/",
        DispenseJobViewSet.as_view({"post": "mark_failed"}),
        name="robotics-job-mark-failed",
    ),
    path(
        "events/",
        RobotEventViewSet.as_view({"get": "list", "post": "create"}),
        name="robotics-event-list",
    ),
    path(
        "events/<uuid:pk>/",
        RobotEventViewSet.as_view(
            {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
        ),
        name="robotics-event-detail",
    ),
]
