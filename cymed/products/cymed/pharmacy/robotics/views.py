"""CyMed Pharmacy robotics viewsets."""
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from . import services
from .models import DispenseJob, RobotBinInventory, RobotDevice, RobotEvent
from .serializers import (
    DispenseJobSerializer,
    RobotBinInventorySerializer,
    RobotDeviceSerializer,
    RobotEventSerializer,
)


class RobotDeviceViewSet(viewsets.ModelViewSet):
    queryset = RobotDevice.objects.all()
    serializer_class = RobotDeviceSerializer

    @action(detail=True, methods=["post"], url_path="heartbeat")
    def heartbeat(self, request, pk=None):
        device = services.heartbeat(device_id=pk, payload=request.data.get("payload"))
        return Response(RobotDeviceSerializer(device).data)

    @action(detail=True, methods=["post"], url_path="dispatch-dispense")
    def dispatch_dispense(self, request, pk=None):
        job = services.dispatch_dispense(
            device_id=pk,
            order_id=request.data["order_id"],
            drug_id=request.data.get("drug_id"),
            drug_name=request.data["drug_name"],
            qty=int(request.data["qty"]),
            patient_profile_id=request.data.get("patient_profile_id"),
        )
        return Response(DispenseJobSerializer(job).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="restock")
    def restock(self, request, pk=None):
        bin_row = services.restock(
            device_id=pk,
            bin_code=request.data["bin_code"],
            drug_id=request.data.get("drug_id"),
            drug_name=request.data["drug_name"],
            qty=int(request.data["qty"]),
            lot_number=request.data.get("lot_number", ""),
            expiry_date=request.data.get("expiry_date"),
        )
        return Response(RobotBinInventorySerializer(bin_row).data)

    @action(detail=True, methods=["get"], url_path="lookup-bin")
    def lookup_bin(self, request, pk=None):
        drug_id = request.query_params.get("drug_id")
        bin_row = services.lookup_bin(device_id=pk, drug_id=drug_id)
        if bin_row is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(RobotBinInventorySerializer(bin_row).data)


class RobotBinInventoryViewSet(viewsets.ModelViewSet):
    queryset = RobotBinInventory.objects.all()
    serializer_class = RobotBinInventorySerializer


class DispenseJobViewSet(viewsets.ModelViewSet):
    queryset = DispenseJob.objects.all()
    serializer_class = DispenseJobSerializer

    @action(detail=True, methods=["post"], url_path="mark-completed")
    def mark_completed(self, request, pk=None):
        job = services.mark_completed(
            job_id=pk,
            qty_dispensed=int(request.data.get("qty_dispensed", 0)),
            lot_number=request.data.get("lot_number", ""),
            vendor_reference=request.data.get("vendor_reference", ""),
        )
        return Response(DispenseJobSerializer(job).data)

    @action(detail=True, methods=["post"], url_path="mark-failed")
    def mark_failed(self, request, pk=None):
        job = services.mark_failed(job_id=pk, error_message=request.data.get("error_message", ""))
        return Response(DispenseJobSerializer(job).data)


class RobotEventViewSet(viewsets.ModelViewSet):
    queryset = RobotEvent.objects.all()
    serializer_class = RobotEventSerializer
