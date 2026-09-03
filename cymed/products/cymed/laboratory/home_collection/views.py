"""DRF viewsets for the home_collection sub-app."""

from __future__ import annotations

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from . import services
from .models import (
    HomeCollectionBooking,
    HomeCollectionEvent,
    HomeCollectionSlot,
    Phlebotomist,
)
from .serializers import (
    HomeCollectionBookingSerializer,
    HomeCollectionEventSerializer,
    HomeCollectionSlotSerializer,
    PhlebotomistSerializer,
)


class PhlebotomistViewSet(viewsets.ModelViewSet):
    queryset = Phlebotomist.objects.all()
    serializer_class = PhlebotomistSerializer


class HomeCollectionSlotViewSet(viewsets.ModelViewSet):
    queryset = HomeCollectionSlot.objects.all()
    serializer_class = HomeCollectionSlotSerializer

    @action(detail=False, methods=["post"], url_path="open")
    def open_slot(self, request):
        data = request.data
        slot = services.open_slot(
            tenant_id=data["tenant_id"],
            phlebotomist_id=data["phlebotomist_id"],
            date=data["date"],
            start_time=data["start_time"],
            end_time=data["end_time"],
            capacity=int(data.get("capacity", 1)),
        )
        return Response(HomeCollectionSlotSerializer(slot).data, status=status.HTTP_201_CREATED)


class HomeCollectionBookingViewSet(viewsets.ModelViewSet):
    queryset = HomeCollectionBooking.objects.all()
    serializer_class = HomeCollectionBookingSerializer

    @action(detail=False, methods=["post"], url_path="book")
    def book(self, request):
        data = request.data
        booking = services.book_home_collection(
            tenant_id=data["tenant_id"],
            patient_profile_id=data["patient_profile_id"],
            slot_id=data["slot_id"],
            address=data.get("address", {}),
            lat=data.get("lat"),
            lng=data.get("lng"),
            tests_requested=data.get("tests_requested", []),
            fasting_required=bool(data.get("fasting_required", False)),
            special_instructions=data.get("special_instructions", ""),
            order_id=data.get("order_id"),
        )
        return Response(HomeCollectionBookingSerializer(booking).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="assign")
    def assign(self, request, pk=None):
        booking = services.assign_phlebotomist(
            booking_id=pk,
            phlebotomist_id=request.data["phlebotomist_id"],
        )
        return Response(HomeCollectionBookingSerializer(booking).data)

    @action(detail=True, methods=["post"], url_path="status")
    def status_update(self, request, pk=None):
        data = request.data
        booking = services.update_status(
            booking_id=pk,
            status=data["status"],
            lat=data.get("lat"),
            lng=data.get("lng"),
            note=data.get("note", ""),
        )
        return Response(HomeCollectionBookingSerializer(booking).data)

    @action(detail=True, methods=["post"], url_path="complete")
    def complete(self, request, pk=None):
        data = request.data
        booking = services.complete_collection(
            booking_id=pk,
            specimen_barcodes=data.get("specimen_barcodes", []),
            proof=data.get("proof", {}),
        )
        return Response(HomeCollectionBookingSerializer(booking).data)

    @action(detail=True, methods=["post"], url_path="cancel")
    def cancel(self, request, pk=None):
        data = request.data
        booking = services.cancel_booking(
            booking_id=pk,
            reason=data.get("reason", ""),
            by_patient=bool(data.get("by_patient", False)),
        )
        return Response(HomeCollectionBookingSerializer(booking).data)


class HomeCollectionEventViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = HomeCollectionEvent.objects.all()
    serializer_class = HomeCollectionEventSerializer
