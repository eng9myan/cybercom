"""ViewSets for CyMed Imaging patient booking."""

from __future__ import annotations

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from . import services
from .models import BookableStudy, ImagingBooking, ImagingSlot, ModalityRoom
from .serializers import (
    BookableStudySerializer,
    ImagingBookingSerializer,
    ImagingSlotSerializer,
    ModalityRoomSerializer,
)


class BookableStudyViewSet(viewsets.ModelViewSet):
    queryset = BookableStudy.objects.all()
    serializer_class = BookableStudySerializer


class ModalityRoomViewSet(viewsets.ModelViewSet):
    queryset = ModalityRoom.objects.all()
    serializer_class = ModalityRoomSerializer


class ImagingSlotViewSet(viewsets.ModelViewSet):
    queryset = ImagingSlot.objects.all()
    serializer_class = ImagingSlotSerializer

    @action(detail=False, methods=["post"], url_path="open")
    def open_slot(self, request):
        slot = services.open_slot(
            tenant_id=request.data["tenant_id"],
            room_id=request.data["room_id"],
            date=request.data["date"],
            start_time=request.data["start_time"],
            end_time=request.data["end_time"],
            capacity=int(request.data.get("capacity", 1)),
        )
        return Response(ImagingSlotSerializer(slot).data)


class ImagingBookingViewSet(viewsets.ModelViewSet):
    queryset = ImagingBooking.objects.all()
    serializer_class = ImagingBookingSerializer

    @action(detail=False, methods=["post"], url_path="cart")
    def cart(self, request):
        booking = services.place_booking(
            tenant_id=request.data["tenant_id"],
            patient_profile_id=request.data["patient_profile_id"],
            study_id=request.data["study_id"],
            slot_id=request.data.get("slot_id"),
            referral_url=request.data.get("referral_url", ""),
            referring_provider_id=request.data.get("referring_provider_id"),
        )
        return Response(ImagingBookingSerializer(booking).data)

    @action(detail=False, methods=["post"], url_path="place")
    def place(self, request):
        booking = services.place_booking(
            tenant_id=request.data["tenant_id"],
            patient_profile_id=request.data["patient_profile_id"],
            study_id=request.data["study_id"],
            slot_id=request.data.get("slot_id"),
            referral_url=request.data.get("referral_url", ""),
            referring_provider_id=request.data.get("referring_provider_id"),
        )
        return Response(ImagingBookingSerializer(booking).data)

    @action(detail=True, methods=["post"], url_path="mark-paid")
    def mark_paid(self, request, pk=None):
        booking = services.mark_paid(
            booking_id=pk,
            payment_ref=request.data.get("payment_ref", ""),
        )
        return Response(ImagingBookingSerializer(booking).data)

    @action(detail=True, methods=["post"], url_path="confirm-prep")
    def confirm_prep(self, request, pk=None):
        booking = services.confirm_prep(
            booking_id=pk,
            preparation_ok=bool(request.data.get("preparation_ok", False)),
            fasting_ok=bool(request.data.get("fasting_ok", False)),
        )
        return Response(ImagingBookingSerializer(booking).data)

    @action(detail=True, methods=["post"], url_path="arrived")
    def arrived(self, request, pk=None):
        booking = services.mark_arrived(pk)
        return Response(ImagingBookingSerializer(booking).data)

    @action(detail=True, methods=["post"], url_path="completed")
    def completed(self, request, pk=None):
        booking = services.mark_completed(pk)
        return Response(ImagingBookingSerializer(booking).data)

    @action(detail=True, methods=["post"], url_path="cancel")
    def cancel(self, request, pk=None):
        booking = services.cancel_booking(pk, request.data.get("reason", ""))
        return Response(ImagingBookingSerializer(booking).data)
