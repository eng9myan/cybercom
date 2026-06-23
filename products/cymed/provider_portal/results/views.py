from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from products.cymed.provider_portal.results.models import (
    ProviderResultView,
    ResultTrend,
    CriticalResultAlert,
    ResultAcknowledgement,
)
from products.cymed.provider_portal.results.serializers import (
    ProviderResultViewSerializer,
    ResultTrendSerializer,
    CriticalResultAlertSerializer,
    ResultAcknowledgementSerializer,
)


class ProviderResultViewViewSet(viewsets.ModelViewSet):
    queryset = ProviderResultView.objects.all()
    serializer_class = ProviderResultViewSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = [
        "patient_id", "result_type", "result_status", "is_critical",
        "is_reviewed", "is_acknowledged", "ordering_provider_id",
    ]
    search_fields = ["result_name", "loinc_code", "result_summary", "fhir_diagnostic_report_id"]
    ordering_fields = ["result_date", "created_at"]
    ordering = ["-result_date"]

    def get_queryset(self):
        tenant_id = getattr(self.request, "tenant_id", None)
        if tenant_id:
            return self.queryset.filter(tenant_id=tenant_id)
        return self.queryset.none()


class ResultTrendViewSet(viewsets.ModelViewSet):
    queryset = ResultTrend.objects.all()
    serializer_class = ResultTrendSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["patient_id", "test_code", "loinc_code"]
    search_fields = ["test_name", "test_code", "loinc_code"]
    ordering_fields = ["test_name", "created_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        tenant_id = getattr(self.request, "tenant_id", None)
        if tenant_id:
            return self.queryset.filter(tenant_id=tenant_id)
        return self.queryset.none()


class CriticalResultAlertViewSet(viewsets.ModelViewSet):
    queryset = CriticalResultAlert.objects.all()
    serializer_class = CriticalResultAlertSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["result", "patient_id", "alerted_provider_id", "alert_type", "status"]
    search_fields = ["alerted_provider_name", "result_value", "clinical_significance", "action_taken"]
    ordering_fields = ["created_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        tenant_id = getattr(self.request, "tenant_id", None)
        if tenant_id:
            return self.queryset.filter(tenant_id=tenant_id)
        return self.queryset.none()


class ResultAcknowledgementViewSet(viewsets.ModelViewSet):
    queryset = ResultAcknowledgement.objects.all()
    serializer_class = ResultAcknowledgementSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["result", "provider_id", "action_taken"]
    search_fields = ["provider_name", "provider_type", "action_notes"]
    ordering_fields = ["follow_up_date", "created_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        tenant_id = getattr(self.request, "tenant_id", None)
        if tenant_id:
            return self.queryset.filter(tenant_id=tenant_id)
        return self.queryset.none()
