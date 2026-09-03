"""URL routes for CyMed Imaging patient booking."""

from __future__ import annotations

from django.urls import path

from .views import (
    BookableStudyViewSet,
    ImagingBookingViewSet,
    ImagingSlotViewSet,
    ModalityRoomViewSet,
)


bookable_study_list = BookableStudyViewSet.as_view({"get": "list", "post": "create"})
bookable_study_detail = BookableStudyViewSet.as_view(
    {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
)

modality_room_list = ModalityRoomViewSet.as_view({"get": "list", "post": "create"})
modality_room_detail = ModalityRoomViewSet.as_view(
    {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
)

imaging_slot_list = ImagingSlotViewSet.as_view({"get": "list", "post": "create"})
imaging_slot_detail = ImagingSlotViewSet.as_view(
    {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
)
imaging_slot_open = ImagingSlotViewSet.as_view({"post": "open_slot"})

imaging_booking_list = ImagingBookingViewSet.as_view({"get": "list", "post": "create"})
imaging_booking_detail = ImagingBookingViewSet.as_view(
    {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
)
imaging_booking_cart = ImagingBookingViewSet.as_view({"post": "cart"})
imaging_booking_place = ImagingBookingViewSet.as_view({"post": "place"})
imaging_booking_mark_paid = ImagingBookingViewSet.as_view({"post": "mark_paid"})
imaging_booking_confirm_prep = ImagingBookingViewSet.as_view({"post": "confirm_prep"})
imaging_booking_arrived = ImagingBookingViewSet.as_view({"post": "arrived"})
imaging_booking_completed = ImagingBookingViewSet.as_view({"post": "completed"})
imaging_booking_cancel = ImagingBookingViewSet.as_view({"post": "cancel"})


urlpatterns = [
    path("bookable-studies/", bookable_study_list, name="cymed-img-bookable-study-list"),
    path("bookable-studies/<uuid:pk>/", bookable_study_detail, name="cymed-img-bookable-study-detail"),
    path("modality-rooms/", modality_room_list, name="cymed-img-modality-room-list"),
    path("modality-rooms/<uuid:pk>/", modality_room_detail, name="cymed-img-modality-room-detail"),
    path("slots/", imaging_slot_list, name="cymed-img-slot-list"),
    path("slots/<uuid:pk>/", imaging_slot_detail, name="cymed-img-slot-detail"),
    path("slots/open/", imaging_slot_open, name="cymed-img-slot-open"),
    path("bookings/", imaging_booking_list, name="cymed-img-booking-list"),
    path("bookings/<uuid:pk>/", imaging_booking_detail, name="cymed-img-booking-detail"),
    path("bookings/cart/", imaging_booking_cart, name="cymed-img-booking-cart"),
    path("bookings/place/", imaging_booking_place, name="cymed-img-booking-place"),
    path("bookings/<uuid:pk>/mark-paid/", imaging_booking_mark_paid, name="cymed-img-booking-mark-paid"),
    path("bookings/<uuid:pk>/confirm-prep/", imaging_booking_confirm_prep, name="cymed-img-booking-confirm-prep"),
    path("bookings/<uuid:pk>/arrived/", imaging_booking_arrived, name="cymed-img-booking-arrived"),
    path("bookings/<uuid:pk>/completed/", imaging_booking_completed, name="cymed-img-booking-completed"),
    path("bookings/<uuid:pk>/cancel/", imaging_booking_cancel, name="cymed-img-booking-cancel"),
]
