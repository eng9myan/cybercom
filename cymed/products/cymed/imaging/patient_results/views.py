"""ViewSets for patient imaging results sub-app."""
from __future__ import annotations

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from . import services
from .models import (
    ImageAccessGrant,
    ReportAcknowledgement,
    ReportDownload,
    ReportRelease,
)
from .serializers import (
    ImageAccessGrantSerializer,
    ReportAcknowledgementSerializer,
    ReportDownloadSerializer,
    ReportReleaseSerializer,
)


class ReportReleaseViewSet(viewsets.ModelViewSet):
    queryset = ReportRelease.objects.all()
    serializer_class = ReportReleaseSerializer

    @action(detail=False, methods=["post"], url_path="release")
    def release(self, request):
        data = request.data
        release = services.release_report(
            tenant_id=data["tenant_id"],
            patient_profile_id=data["patient_profile_id"],
            study_instance_uid=data["study_instance_uid"],
            report_id=data.get("report_id"),
            released_by_profile_id=data.get("released_by_profile_id"),
            release_kind=data.get("release_kind", "full"),
            channels=data.get("channels"),
            requires_counselling=data.get("requires_counselling", False),
            incidental_flag=data.get("incidental_flag", False),
        )
        return Response(ReportReleaseSerializer(release).data)

    @action(detail=True, methods=["post"], url_path="retract")
    def retract(self, request, pk=None):
        release = services.retract(
            release_id=pk,
            reason=request.data.get("reason", ""),
        )
        return Response(ReportReleaseSerializer(release).data)

    @action(detail=True, methods=["post"], url_path="viewer-link")
    def viewer_link(self, request, pk=None):
        grant = services.create_viewer_link(
            release_id=pk,
            kind=request.data.get("kind", "viewer_link"),
            expires_in_hours=int(request.data.get("expires_in_hours", 72)),
            max_downloads=int(request.data.get("max_downloads", -1)),
        )
        return Response(ImageAccessGrantSerializer(grant).data)

    @action(detail=True, methods=["post"], url_path="record-download")
    def record_download(self, request, pk=None):
        dl = services.record_download(
            release_id=pk,
            kind=request.data.get("kind", "pdf"),
            downloaded_by_profile_id=request.data.get("downloaded_by_profile_id"),
            ip_address=request.data.get("ip_address", ""),
        )
        return Response(ReportDownloadSerializer(dl).data)

    @action(detail=True, methods=["post"], url_path="acknowledge")
    def acknowledge(self, request, pk=None):
        ack = services.acknowledge(
            release_id=pk,
            patient_profile_id=request.data["patient_profile_id"],
            question_asked=request.data.get("question_asked", ""),
        )
        return Response(ReportAcknowledgementSerializer(ack).data)

    @action(detail=True, methods=["post"], url_path="generate-pdf")
    def generate_pdf(self, request, pk=None):
        data = services.generate_pdf(release_id=pk)
        return Response({"bytes_length": len(data)})


class ImageAccessGrantViewSet(viewsets.ModelViewSet):
    queryset = ImageAccessGrant.objects.all()
    serializer_class = ImageAccessGrantSerializer


class ReportDownloadViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ReportDownload.objects.all()
    serializer_class = ReportDownloadSerializer


class ReportAcknowledgementViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ReportAcknowledgement.objects.all()
    serializer_class = ReportAcknowledgementSerializer
