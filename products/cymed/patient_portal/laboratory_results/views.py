from rest_framework import filters, permissions, viewsets

from .models import (
    CriticalResultAcknowledgement,
    LabResultShareLink,
    LabResultTrend,
    LabResultView,
)
from .serializers import (
    CriticalResultAcknowledgementSerializer,
    LabResultShareLinkSerializer,
    LabResultTrendSerializer,
    LabResultViewSerializer,
)


class LabResultViewViewSet(viewsets.ModelViewSet):
    serializer_class = LabResultViewSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["test_name", "test_code", "loinc_code", "lab_name", "order_number"]
    ordering_fields = ["resulted_at", "collected_at", "created_at", "result_status"]
    ordering = ["-resulted_at"]

    def get_queryset(self):
        qs = LabResultView.objects.filter(tenant_id=self.request.tenant_id)
        patient_id = self.request.query_params.get("patient_id")
        account_id = self.request.query_params.get("account_id")
        result_status = self.request.query_params.get("result_status")
        is_critical = self.request.query_params.get("is_critical")
        is_viewed = self.request.query_params.get("is_viewed")

        if patient_id:
            qs = qs.filter(patient_id=patient_id)
        if account_id:
            qs = qs.filter(account_id=account_id)
        if result_status:
            qs = qs.filter(result_status=result_status)
        if is_critical is not None:
            qs = qs.filter(is_critical=is_critical.lower() == "true")
        if is_viewed is not None:
            qs = qs.filter(is_viewed=is_viewed.lower() == "true")
        return qs


class LabResultTrendViewSet(viewsets.ModelViewSet):
    serializer_class = LabResultTrendSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["test_name", "test_code", "loinc_code"]
    ordering_fields = ["last_updated", "test_name", "test_code"]
    ordering = ["-last_updated"]

    def get_queryset(self):
        qs = LabResultTrend.objects.filter(tenant_id=self.request.tenant_id)
        patient_id = self.request.query_params.get("patient_id")
        account_id = self.request.query_params.get("account_id")
        test_code = self.request.query_params.get("test_code")

        if patient_id:
            qs = qs.filter(patient_id=patient_id)
        if account_id:
            qs = qs.filter(account_id=account_id)
        if test_code:
            qs = qs.filter(test_code=test_code)
        return qs


class CriticalResultAcknowledgementViewSet(viewsets.ModelViewSet):
    serializer_class = CriticalResultAcknowledgementSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ["acknowledged_at", "action_taken"]
    ordering = ["-acknowledged_at"]

    def get_queryset(self):
        qs = CriticalResultAcknowledgement.objects.filter(tenant_id=self.request.tenant_id)
        patient_id = self.request.query_params.get("patient_id")
        account_id = self.request.query_params.get("account_id")
        lab_result_id = self.request.query_params.get("lab_result_id")

        if patient_id:
            qs = qs.filter(patient_id=patient_id)
        if account_id:
            qs = qs.filter(account_id=account_id)
        if lab_result_id:
            qs = qs.filter(lab_result_id=lab_result_id)
        return qs


class LabResultShareLinkViewSet(viewsets.ModelViewSet):
    serializer_class = LabResultShareLinkSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ["valid_until", "created_at", "access_count"]
    ordering = ["-created_at"]

    def get_queryset(self):
        qs = LabResultShareLink.objects.filter(tenant_id=self.request.tenant_id)
        account_id = self.request.query_params.get("account_id")
        lab_result_id = self.request.query_params.get("lab_result_id")
        is_revoked = self.request.query_params.get("is_revoked")

        if account_id:
            qs = qs.filter(account_id=account_id)
        if lab_result_id:
            qs = qs.filter(lab_result_id=lab_result_id)
        if is_revoked is not None:
            qs = qs.filter(is_revoked=is_revoked.lower() == "true")
        return qs
