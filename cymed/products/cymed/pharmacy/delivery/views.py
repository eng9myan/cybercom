"""CyMed Pharmacy Delivery viewsets."""
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from . import services
from .models import Courier, DeliveryJob, DeliveryStatusEvent, Rider
from .serializers import (
    CourierSerializer,
    DeliveryJobSerializer,
    DeliveryStatusEventSerializer,
    RiderSerializer,
)


class CourierViewSet(viewsets.ModelViewSet):
    queryset = Courier.objects.all()
    serializer_class = CourierSerializer


class RiderViewSet(viewsets.ModelViewSet):
    queryset = Rider.objects.all()
    serializer_class = RiderSerializer


class DeliveryJobViewSet(viewsets.ModelViewSet):
    queryset = DeliveryJob.objects.all()
    serializer_class = DeliveryJobSerializer

    @action(detail=False, methods=["post"], url_path="create-job")
    def create_job(self, request):
        job = services.create_job(**request.data)
        return Response(DeliveryJobSerializer(job).data)

    @action(detail=True, methods=["post"], url_path="assign-rider")
    def assign_rider(self, request, pk=None):
        rider_id = request.data.get("rider_id")
        job = services.assign_rider(job_id=pk, rider_id=rider_id)
        return Response(DeliveryJobSerializer(job).data)

    @action(detail=True, methods=["post"], url_path="update-status")
    def update_status(self, request, pk=None):
        job = services.update_status(
            job_id=pk,
            status=request.data.get("status"),
            lat=request.data.get("lat"),
            lng=request.data.get("lng"),
            note=request.data.get("note", ""),
        )
        return Response(DeliveryJobSerializer(job).data)

    @action(detail=True, methods=["post"], url_path="upload-proof")
    def upload_proof(self, request, pk=None):
        job = services.upload_proof(
            job_id=pk,
            photo_url=request.data.get("photo_url", ""),
            signature_url=request.data.get("signature_url", ""),
            otp_code=request.data.get("otp_code"),
        )
        return Response(DeliveryJobSerializer(job).data)

    @action(detail=True, methods=["post"], url_path="dispatch")
    def dispatch_action(self, request, pk=None):
        result = services.dispatch_to_provider(pk)
        return Response({"tracking_id": result})

    @action(detail=False, methods=["get"], url_path="kpi-snapshot")
    def kpi_snapshot(self, request):
        tenant_id = request.query_params.get("tenant_id")
        return Response(services.kpi_snapshot(tenant_id))


class DeliveryStatusEventViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = DeliveryStatusEvent.objects.all()
    serializer_class = DeliveryStatusEventSerializer
