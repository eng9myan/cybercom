"""DRF viewsets exposing patient results release, notification, and acknowledgement APIs."""
from __future__ import annotations

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from . import services
from .models import (
    ResultAcknowledgement,
    ResultDownload,
    ResultNotification,
    ResultRelease,
)
from .serializers import (
    ResultAcknowledgementSerializer,
    ResultDownloadSerializer,
    ResultNotificationSerializer,
    ResultReleaseSerializer,
)


class ResultReleaseViewSet(viewsets.ModelViewSet):
    queryset = ResultRelease.objects.all()
    serializer_class = ResultReleaseSerializer

    @action(detail=False, methods=["post"], url_path="release")
    def release(self, request):
        data = request.data
        release = services.release_result(
            tenant_id=data.get("tenant_id"),
            order_id=data.get("order_id"),
            result_id=data.get("result_id"),
            patient_profile_id=data.get("patient_profile_id"),
            released_by_profile_id=data.get("released_by_profile_id"),
            release_kind=data.get("release_kind", "full"),
            channels=data.get("channels"),
            requires_counselling=data.get("requires_counselling", False),
            counselling_note=data.get("counselling_note", ""),
        )
        return Response(ResultReleaseSerializer(release).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="retract")
    def retract(self, request, pk=None):
        release = services.retract_release(
            release_id=pk,
            reason=request.data.get("reason", ""),
        )
        return Response(ResultReleaseSerializer(release).data)

    @action(detail=True, methods=["post"], url_path="notify")
    def notify(self, request, pk=None):
        notifications = services.notify_patient(
            release_id=pk,
            channels=request.data.get("channels", []),
            recipient_map=request.data.get("recipient_map", {}),
        )
        return Response(ResultNotificationSerializer(notifications, many=True).data)

    @action(detail=True, methods=["post"], url_path="acknowledge")
    def acknowledge(self, request, pk=None):
        ack = services.acknowledge(
            release_id=pk,
            patient_profile_id=request.data.get("patient_profile_id"),
            question_asked=request.data.get("question_asked", ""),
        )
        return Response(ResultAcknowledgementSerializer(ack).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="download-pdf")
    def download_pdf(self, request, pk=None):
        payload = services.generate_pdf(release_id=pk)
        services.record_download(
            release_id=pk,
            downloaded_by_profile_id=request.data.get("downloaded_by_profile_id"),
            kind="pdf",
            ip_address=request.META.get("REMOTE_ADDR", ""),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
        )
        return Response({"content": payload.decode("latin-1"), "content_type": "application/pdf"})


class ResultDownloadViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ResultDownload.objects.all()
    serializer_class = ResultDownloadSerializer


class ResultNotificationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ResultNotification.objects.all()
    serializer_class = ResultNotificationSerializer


class ResultAcknowledgementViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ResultAcknowledgement.objects.all()
    serializer_class = ResultAcknowledgementSerializer
