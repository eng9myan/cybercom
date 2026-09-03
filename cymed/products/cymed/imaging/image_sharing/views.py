"""ViewSets for the image_sharing sub-app."""
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from . import services
from .models import ExternalImport, ShareAccessLog, ShareableStudy, ShareLink
from .serializers import (
    ExternalImportSerializer,
    ShareAccessLogSerializer,
    ShareableStudySerializer,
    ShareLinkSerializer,
)


class ShareableStudyViewSet(viewsets.ModelViewSet):
    queryset = ShareableStudy.objects.all()
    serializer_class = ShareableStudySerializer

    @action(detail=False, methods=["post"], url_path="index")
    def index_study(self, request):
        data = request.data
        study = services.index_study(
            tenant_id=data["tenant_id"],
            patient_profile_id=data["patient_profile_id"],
            study_instance_uid=data["study_instance_uid"],
            modality=data.get("modality", ""),
            study_date=data.get("study_date"),
            description=data.get("description", ""),
            original_facility_id=data.get("original_facility_id"),
            size_mb=data.get("size_mb", 0),
            image_count=data.get("image_count", 0),
            series_count=data.get("series_count", 0),
        )
        return Response(ShareableStudySerializer(study).data)


class ShareLinkViewSet(viewsets.ModelViewSet):
    queryset = ShareLink.objects.all()
    serializer_class = ShareLinkSerializer

    @action(detail=False, methods=["post"], url_path="create-link")
    def create_link(self, request):
        data = request.data
        link = services.create_share_link(
            tenant_id=data["tenant_id"],
            shareable_study_id=data["shareable_study_id"],
            created_by_profile_id=data.get("created_by_profile_id"),
            recipient_kind=data["recipient_kind"],
            recipient_email=data.get("recipient_email", ""),
            recipient_name=data.get("recipient_name", ""),
            recipient_organization=data.get("recipient_organization", ""),
            expires_in_hours=int(data.get("expires_in_hours", 168)),
            max_views=int(data.get("max_views", -1)),
            passphrase=data.get("passphrase", ""),
            download_enabled=bool(data.get("download_enabled", True)),
            watermark_text=data.get("watermark_text", ""),
        )
        return Response(ShareLinkSerializer(link).data)

    @action(detail=False, methods=["post"], url_path="open")
    def open_link(self, request):
        data = request.data
        link = services.open_link(
            token=data["token"],
            passphrase=data.get("passphrase", ""),
            ip_address=data.get("ip_address", ""),
            user_agent=data.get("user_agent", ""),
        )
        return Response(ShareLinkSerializer(link).data)

    @action(detail=False, methods=["post"], url_path="download")
    def download(self, request):
        data = request.data
        log = services.record_download(
            token=data["token"],
            ip_address=data.get("ip_address", ""),
            user_agent=data.get("user_agent", ""),
        )
        return Response(ShareAccessLogSerializer(log).data)

    @action(detail=True, methods=["post"], url_path="revoke")
    def revoke(self, request, pk=None):
        reason = request.data.get("reason", "")
        link = services.revoke_link(link_id=pk, reason=reason)
        return Response(ShareLinkSerializer(link).data)


class ShareAccessLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ShareAccessLog.objects.all()
    serializer_class = ShareAccessLogSerializer


class ExternalImportViewSet(viewsets.ModelViewSet):
    queryset = ExternalImport.objects.all()
    serializer_class = ExternalImportSerializer

    @action(detail=False, methods=["post"], url_path="import")
    def import_study(self, request):
        data = request.data
        record = services.import_external_study(
            tenant_id=data["tenant_id"],
            patient_profile_id=data.get("patient_profile_id"),
            source_kind=data.get("source_kind", "cd"),
            original_facility_name=data.get("original_facility_name", ""),
            size_mb=data.get("size_mb", 0),
            image_count=data.get("image_count", 0),
            imported_by_profile_id=data.get("imported_by_profile_id"),
            study_instance_uid=data.get("study_instance_uid", ""),
        )
        return Response(ExternalImportSerializer(record).data)
