"""URL routes for the home_collection sub-app."""

from __future__ import annotations

from django.urls import path

from .views import (
    HomeCollectionBookingViewSet,
    HomeCollectionEventViewSet,
    HomeCollectionSlotViewSet,
    PhlebotomistViewSet,
)

phlebotomist_list = PhlebotomistViewSet.as_view({"get": "list", "post": "create"})
phlebotomist_detail = PhlebotomistViewSet.as_view(
    {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
)

slot_list = HomeCollectionSlotViewSet.as_view({"get": "list", "post": "create"})
slot_detail = HomeCollectionSlotViewSet.as_view(
    {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
)
slot_open = HomeCollectionSlotViewSet.as_view({"post": "open_slot"})

booking_list = HomeCollectionBookingViewSet.as_view({"get": "list", "post": "create"})
booking_detail = HomeCollectionBookingViewSet.as_view(
    {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
)
booking_book = HomeCollectionBookingViewSet.as_view({"post": "book"})
booking_assign = HomeCollectionBookingViewSet.as_view({"post": "assign"})
booking_status = HomeCollectionBookingViewSet.as_view({"post": "status_update"})
booking_complete = HomeCollectionBookingViewSet.as_view({"post": "complete"})
booking_cancel = HomeCollectionBookingViewSet.as_view({"post": "cancel"})

event_list = HomeCollectionEventViewSet.as_view({"get": "list"})
event_detail = HomeCollectionEventViewSet.as_view({"get": "retrieve"})

urlpatterns = [
    path("phlebotomists/", phlebotomist_list, name="home-collection-phlebotomist-list"),
    path("phlebotomists/<uuid:pk>/", phlebotomist_detail, name="home-collection-phlebotomist-detail"),
    path("slots/", slot_list, name="home-collection-slot-list"),
    path("slots/<uuid:pk>/", slot_detail, name="home-collection-slot-detail"),
    path("slots/open/", slot_open, name="home-collection-slot-open"),
    path("bookings/", booking_list, name="home-collection-booking-list"),
    path("bookings/<uuid:pk>/", booking_detail, name="home-collection-booking-detail"),
    path("bookings/book/", booking_book, name="home-collection-booking-book"),
    path("bookings/<uuid:pk>/assign/", booking_assign, name="home-collection-booking-assign"),
    path("bookings/<uuid:pk>/status/", booking_status, name="home-collection-booking-status"),
    path("bookings/<uuid:pk>/complete/", booking_complete, name="home-collection-booking-complete"),
    path("bookings/<uuid:pk>/cancel/", booking_cancel, name="home-collection-booking-cancel"),
    path("events/", event_list, name="home-collection-event-list"),
    path("events/<uuid:pk>/", event_detail, name="home-collection-event-detail"),
]
