from rest_framework import filters, permissions, viewsets

from .models import (
    ImagingReportAccess,
    ImagingResultView,
    ImagingShareLink,
    ImagingStudyMetadata,
)
from .serializers import (
    ImagingReportAccessSerializer,
    ImagingResultViewSerializer,
    ImagingShareLinkSerializer,
    ImagingStudyMetadataSerializer,
)


class ImagingResultViewViewSet(viewsets.ModelViewSet):
    serializer_class = ImagingResultViewSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = [
        "study_description",
        "body_part",
        "modality",
        "imaging_center_name",
        "accession_number",
        "order_number",
    ]
    ordering_fields = ["study_date", "created_at", "report_status", "modality"]
    ordering = ["-study_date"]

    def get_queryset(self):
        qs = ImagingResultView.objects.filter(tenant_id=self.request.tenant_id)
        patient_id = self.request.query_params.get("patient_id")
        account_id = self.request.query_params.get("account_id")
        modality = self.request.query_params.get("modality")
        report_status = self.request.query_params.get("report_status")
        has_critical_finding = self.request.query_params.get("has_critical_finding")
        is_viewed = self.request.query_params.get("is_viewed")

        if patient_id:
            qs = qs.filter(patient_id=patient_id)
        if account_id:
            qs = qs.filter(account_id=account_id)
        if modality:
            qs = qs.filter(modality=modality)
        if report_status:
            qs = qs.filter(report_status=report_status)
        if has_critical_finding is not None:
            qs = qs.filter(has_critical_finding=has_critical_finding.lower() == "true")
        if is_viewed is not None:
            qs = qs.filter(is_viewed=is_viewed.lower() == "true")
        return qs


class ImagingStudyMetadataViewSet(viewsets.ModelViewSet):
    serializer_class = ImagingStudyMetadataSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ["series_number", "modality"]
    ordering = ["series_number"]

    def get_queryset(self):
        qs = ImagingStudyMetadata.objects.filter(tenant_id=self.request.tenant_id)
        imaging_result_id = self.request.query_params.get("imaging_result_id")
        modality = self.request.query_params.get("modality")

        if imaging_result_id:
            qs = qs.filter(imaging_result_id=imaging_result_id)
        if modality:
            qs = qs.filter(modality=modality)
        return qs


class ImagingReportAccessViewSet(viewsets.ModelViewSet):
    serializer_class = ImagingReportAccessSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ["accessed_at", "access_type"]
    ordering = ["-accessed_at"]

    def get_queryset(self):
        qs = ImagingReportAccess.objects.filter(tenant_id=self.request.tenant_id)
        patient_id = self.request.query_params.get("patient_id")
        account_id = self.request.query_params.get("account_id")
        imaging_result_id = self.request.query_params.get("imaging_result_id")
        access_type = self.request.query_params.get("access_type")

        if patient_id:
            qs = qs.filter(patient_id=patient_id)
        if account_id:
            qs = qs.filter(account_id=account_id)
        if imaging_result_id:
            qs = qs.filter(imaging_result_id=imaging_result_id)
        if access_type:
            qs = qs.filter(access_type=access_type)
        return qs


class ImagingShareLinkViewSet(viewsets.ModelViewSet):
    serializer_class = ImagingShareLinkSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ["valid_until", "created_at", "access_count"]
    ordering = ["-created_at"]

    def get_queryset(self):
        qs = ImagingShareLink.objects.filter(tenant_id=self.request.tenant_id)
        account_id = self.request.query_params.get("account_id")
        imaging_result_id = self.request.query_params.get("imaging_result_id")
        share_type = self.request.query_params.get("share_type")
        is_revoked = self.request.query_params.get("is_revoked")

        if account_id:
            qs = qs.filter(account_id=account_id)
        if imaging_result_id:
            qs = qs.filter(imaging_result_id=imaging_result_id)
        if share_type:
            qs = qs.filter(share_type=share_type)
        if is_revoked is not None:
            qs = qs.filter(is_revoked=is_revoked.lower() == "true")
        return qs
