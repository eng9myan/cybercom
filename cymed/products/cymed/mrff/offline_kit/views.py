"""ViewSets for CyMed MRFF offline_kit sub-app."""
from __future__ import annotations

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from . import services
from .models import (
    ConflictResolution,
    OfflineCdssRun,
    OfflineDevice,
    OfflineIntake,
    SyncQueueItem,
)
from .serializers import (
    ConflictResolutionSerializer,
    OfflineCdssRunSerializer,
    OfflineDeviceSerializer,
    OfflineIntakeSerializer,
    SyncQueueItemSerializer,
)


class OfflineDeviceViewSet(viewsets.ModelViewSet):
    queryset = OfflineDevice.objects.all()
    serializer_class = OfflineDeviceSerializer

    @action(detail=False, methods=["post"], url_path="register")
    def register(self, request):
        device = services.register_device(
            tenant_id=request.data.get("tenant_id"),
            device_uuid=request.data.get("device_uuid"),
            device_kind=request.data.get("device_kind"),
            operator_profile_id=request.data.get("operator_profile_id"),
            facility_id=request.data.get("facility_id"),
            accho_flag=bool(request.data.get("accho_flag", False)),
            app_version=request.data.get("app_version", ""),
            platform=request.data.get("platform", ""),
        )
        return Response(OfflineDeviceSerializer(device).data)

    @action(detail=True, methods=["post"], url_path="sync-next-batch")
    def sync_next_batch(self, request, pk=None):
        limit = int(request.data.get("limit", 50))
        result = services.sync_next_batch(device_id=pk, limit=limit)
        return Response(result)


class OfflineIntakeViewSet(viewsets.ModelViewSet):
    queryset = OfflineIntake.objects.all()
    serializer_class = OfflineIntakeSerializer

    @action(detail=False, methods=["post"], url_path="capture")
    def capture(self, request):
        intake = services.capture_intake(
            tenant_id=request.data.get("tenant_id"),
            device_id=request.data.get("device_id"),
            local_id=request.data.get("local_id"),
            patient_snapshot=request.data.get("patient_snapshot", {}),
            chief_complaint=request.data.get("chief_complaint", ""),
            vitals=request.data.get("vitals"),
            history=request.data.get("history"),
            encounter_kind=request.data.get("encounter_kind", "routine"),
            accho_specific=request.data.get("accho_specific"),
        )
        return Response(OfflineIntakeSerializer(intake).data)

    @action(detail=True, methods=["post"], url_path="record-cdss")
    def record_cdss(self, request, pk=None):
        run = services.record_offline_cdss(
            intake_id=pk,
            kind=request.data.get("kind"),
            score=request.data.get("score"),
            band=request.data.get("band"),
            recommendations=request.data.get("recommendations"),
        )
        return Response(OfflineCdssRunSerializer(run).data)


class SyncQueueItemViewSet(viewsets.ModelViewSet):
    queryset = SyncQueueItem.objects.all()
    serializer_class = SyncQueueItemSerializer

    @action(detail=False, methods=["post"], url_path="enqueue")
    def enqueue(self, request):
        item = services.enqueue_payload(
            tenant_id=request.data.get("tenant_id"),
            device_id=request.data.get("device_id"),
            payload_kind=request.data.get("payload_kind"),
            local_ref=request.data.get("local_ref"),
            payload=request.data.get("payload", {}),
        )
        return Response(SyncQueueItemSerializer(item).data)


class ConflictResolutionViewSet(viewsets.ModelViewSet):
    queryset = ConflictResolution.objects.all()
    serializer_class = ConflictResolutionSerializer

    @action(detail=True, methods=["post"], url_path="resolve")
    def resolve(self, request, pk=None):
        resolution = services.resolve_conflict(
            resolution_id=pk,
            strategy=request.data.get("strategy"),
            resolved_payload=request.data.get("resolved_payload"),
            resolved_by_profile_id=request.data.get("resolved_by_profile_id"),
        )
        return Response(ConflictResolutionSerializer(resolution).data)


class OfflineCdssRunViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = OfflineCdssRun.objects.all()
    serializer_class = OfflineCdssRunSerializer
