"""URL routing for CyMed Laboratory Online Test Booking."""
from django.urls import path

from .views import (
    BookableTestViewSet,
    LabAppointmentSlotViewSet,
    LabBookingViewSet,
    LabPackageViewSet,
)

urlpatterns = [
    path(
        "bookable-tests/",
        BookableTestViewSet.as_view({"get": "list", "post": "create"}),
        name="bookable-test-list",
    ),
    path(
        "bookable-tests/<uuid:pk>/",
        BookableTestViewSet.as_view(
            {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
        ),
        name="bookable-test-detail",
    ),
    path(
        "packages/",
        LabPackageViewSet.as_view({"get": "list", "post": "create"}),
        name="lab-package-list",
    ),
    path(
        "packages/<uuid:pk>/",
        LabPackageViewSet.as_view(
            {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
        ),
        name="lab-package-detail",
    ),
    path(
        "slots/",
        LabAppointmentSlotViewSet.as_view({"get": "list", "post": "create"}),
        name="lab-slot-list",
    ),
    path(
        "slots/<uuid:pk>/",
        LabAppointmentSlotViewSet.as_view(
            {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
        ),
        name="lab-slot-detail",
    ),
    path(
        "slots/open/",
        LabAppointmentSlotViewSet.as_view({"post": "open"}),
        name="lab-slot-open",
    ),
    path(
        "bookings/",
        LabBookingViewSet.as_view({"get": "list", "post": "create"}),
        name="lab-booking-list",
    ),
    path(
        "bookings/<uuid:pk>/",
        LabBookingViewSet.as_view(
            {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
        ),
        name="lab-booking-detail",
    ),
    path(
        "bookings/cart/",
        LabBookingViewSet.as_view({"post": "cart"}),
        name="lab-booking-cart",
    ),
    path(
        "bookings/place/",
        LabBookingViewSet.as_view({"post": "place"}),
        name="lab-booking-place",
    ),
    path(
        "bookings/<uuid:pk>/mark-paid/",
        LabBookingViewSet.as_view({"post": "mark_paid"}),
        name="lab-booking-mark-paid",
    ),
    path(
        "bookings/<uuid:pk>/schedule/",
        LabBookingViewSet.as_view({"post": "schedule"}),
        name="lab-booking-schedule",
    ),
    path(
        "bookings/<uuid:pk>/cancel/",
        LabBookingViewSet.as_view({"post": "cancel"}),
        name="lab-booking-cancel",
    ),
]
