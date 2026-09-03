"""ViewSets for CyMed Laboratory Online Test Booking."""
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from . import services
from .models import BookableTest, LabAppointmentSlot, LabBooking, LabPackage
from .serializers import (
    BookableTestSerializer,
    LabAppointmentSlotSerializer,
    LabBookingSerializer,
    LabPackageSerializer,
)


class BookableTestViewSet(viewsets.ModelViewSet):
    queryset = BookableTest.objects.all()
    serializer_class = BookableTestSerializer


class LabPackageViewSet(viewsets.ModelViewSet):
    queryset = LabPackage.objects.all()
    serializer_class = LabPackageSerializer


class LabAppointmentSlotViewSet(viewsets.ModelViewSet):
    queryset = LabAppointmentSlot.objects.all()
    serializer_class = LabAppointmentSlotSerializer

    @action(detail=False, methods=["post"], url_path="open")
    def open(self, request):
        slot = services.open_slot(
            tenant_id=request.data.get("tenant_id"),
            facility_id=request.data.get("facility_id"),
            date=request.data.get("date"),
            start_time=request.data.get("start_time"),
            end_time=request.data.get("end_time"),
            capacity=request.data.get("capacity", 1),
            collection_mode=request.data.get("collection_mode", "in_lab"),
        )
        return Response(LabAppointmentSlotSerializer(slot).data, status=status.HTTP_201_CREATED)


class LabBookingViewSet(viewsets.ModelViewSet):
    queryset = LabBooking.objects.all()
    serializer_class = LabBookingSerializer

    @action(detail=False, methods=["post"], url_path="cart")
    def cart(self, request):
        result = services.build_cart(
            tenant_id=request.data.get("tenant_id"),
            patient_profile_id=request.data.get("patient_profile_id"),
            test_ids=request.data.get("test_ids", []),
            package_ids=request.data.get("package_ids", []),
        )
        return Response(result, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"], url_path="place")
    def place(self, request):
        booking = services.place_booking(
            tenant_id=request.data.get("tenant_id"),
            patient_profile_id=request.data.get("patient_profile_id"),
            test_ids=request.data.get("test_ids", []),
            package_ids=request.data.get("package_ids", []),
            slot_id=request.data.get("slot_id"),
            collection_mode=request.data.get("collection_mode", "in_lab"),
        )
        return Response(LabBookingSerializer(booking).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="mark-paid")
    def mark_paid(self, request, pk=None):
        booking = services.mark_paid(
            booking_id=pk,
            payment_ref=request.data.get("payment_ref", ""),
        )
        return Response(LabBookingSerializer(booking).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="schedule")
    def schedule(self, request, pk=None):
        booking = services.schedule_collection(
            booking_id=pk,
            home_collection_booking_id=request.data.get("home_collection_booking_id"),
            slot_id=request.data.get("slot_id"),
        )
        return Response(LabBookingSerializer(booking).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="cancel")
    def cancel(self, request, pk=None):
        booking = services.cancel_booking(
            booking_id=pk,
            reason=request.data.get("reason", ""),
        )
        return Response(LabBookingSerializer(booking).data, status=status.HTTP_200_OK)
