"""DRF viewsets for CyMed Laboratory courier tracking."""

from __future__ import annotations

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from . import services
from .models import ChainOfCustodyEvent, Manifest, Route, Run, TransportTemperature
from .serializers import (
    ChainOfCustodyEventSerializer,
    ManifestSerializer,
    RouteSerializer,
    RunSerializer,
    TransportTemperatureSerializer,
)


class RouteViewSet(viewsets.ModelViewSet):
    queryset = Route.objects.all()
    serializer_class = RouteSerializer


class RunViewSet(viewsets.ModelViewSet):
    queryset = Run.objects.all()
    serializer_class = RunSerializer

    @action(detail=False, methods=["post"], url_path="open")
    def open_run(self, request):
        data = request.data
        run = services.open_run(
            tenant_id=data["tenant_id"],
            route_id=data["route_id"],
            run_date=data["run_date"],
            driver_id=data.get("driver_id"),
            vehicle_plate=data.get("vehicle_plate", ""),
            cold_chain=bool(data.get("cold_chain", False)),
        )
        return Response(RunSerializer(run).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="close")
    def close_run(self, request, pk=None):
        run = services.close_run(run_id=pk)
        return Response(RunSerializer(run).data)

    @action(detail=True, methods=["post"], url_path="generate-manifest")
    def generate_manifest(self, request, pk=None):
        manifest = services.generate_manifest(
            run_id=pk,
            specimen_barcodes=request.data.get("specimen_barcodes", []),
        )
        return Response(ManifestSerializer(manifest).data, status=status.HTTP_201_CREATED)


class ChainOfCustodyEventViewSet(viewsets.ModelViewSet):
    queryset = ChainOfCustodyEvent.objects.all()
    serializer_class = ChainOfCustodyEventSerializer

    @action(detail=False, methods=["post"], url_path="record")
    def record(self, request):
        data = request.data
        event = services.record_custody(
            tenant_id=data["tenant_id"],
            specimen_barcode=data["specimen_barcode"],
            kind=data["kind"],
            order_id=data.get("order_id"),
            run_id=data.get("run_id"),
            actor_profile_id=data.get("actor_profile_id"),
            lat=data.get("lat"),
            lng=data.get("lng"),
            temperature_c=data.get("temperature_c"),
            signature_url=data.get("signature_url", ""),
            note=data.get("note", ""),
        )
        return Response(ChainOfCustodyEventSerializer(event).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["get"], url_path="locate")
    def locate(self, request):
        barcode = request.query_params.get("specimen_barcode", "")
        events = services.locate_specimen(specimen_barcode=barcode)
        return Response(ChainOfCustodyEventSerializer(events, many=True).data)


class TransportTemperatureViewSet(viewsets.ModelViewSet):
    queryset = TransportTemperature.objects.all()
    serializer_class = TransportTemperatureSerializer

    @action(detail=False, methods=["post"], url_path="record")
    def record(self, request):
        data = request.data
        reading = services.record_temperature(
            run_id=data["run_id"],
            specimen_barcode=data["specimen_barcode"],
            temperature_c=data["temperature_c"],
            cold_chain_kind=data.get("cold_chain_kind", "refrigerated"),
        )
        return Response(TransportTemperatureSerializer(reading).data, status=status.HTTP_201_CREATED)


class ManifestViewSet(viewsets.ModelViewSet):
    queryset = Manifest.objects.all()
    serializer_class = ManifestSerializer

    @action(detail=True, methods=["post"], url_path="deliver")
    def deliver(self, request, pk=None):
        manifest = services.deliver_manifest(
            manifest_id=pk,
            receiver_signature_url=request.data.get("receiver_signature_url", ""),
        )
        return Response(ManifestSerializer(manifest).data)
