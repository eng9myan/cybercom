from django.urls import path

from .views import (
    AssignBatchView,
    AssignDriverView,
    OrderTrackingView,
    RecordTrackingEventView,
    RunStatusView,
    ZoneCheckView,
)

urlpatterns = [
    path("zones/check/", ZoneCheckView.as_view(), name="delivery-zone-check"),
    path("assign/", AssignDriverView.as_view(), name="delivery-assign"),
    path("assign/batch/", AssignBatchView.as_view(), name="delivery-assign-batch"),
    path("runs/<uuid:run_id>/", RunStatusView.as_view(), name="delivery-run-status"),
    path("events/", RecordTrackingEventView.as_view(), name="delivery-record-event"),
    path("track/<uuid:order_id>/", OrderTrackingView.as_view(), name="delivery-track"),
]
