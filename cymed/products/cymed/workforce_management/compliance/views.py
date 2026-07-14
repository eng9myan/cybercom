from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated

from .models import (
    ComplianceAuditLog,
    RamadanComplianceRule,
    WardRatioConfig,
    WorkforceComplianceConfig,
)
from .serializers import (
    ComplianceAuditLogSerializer,
    RamadanComplianceRuleSerializer,
    WardRatioConfigSerializer,
    WorkforceComplianceConfigSerializer,
)


class HWMModelViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]

    def get_queryset(self):
        tenant_id = getattr(self.request, "tenant_id", None)
        if tenant_id:
            return self.queryset.filter(tenant_id=tenant_id)
        return self.queryset.none()

    def perform_create(self, serializer):
        tenant_id = getattr(self.request, "tenant_id", None)
        serializer.save(tenant_id=tenant_id)


class WorkforceComplianceConfigViewSet(HWMModelViewSet):
    queryset = WorkforceComplianceConfig.objects.all()
    serializer_class = WorkforceComplianceConfigSerializer
    filterset_fields = ["country_code", "region_code", "accreditation_body", "is_active"]
    ordering_fields = ["country_code", "region_code", "created_at"]


class RamadanComplianceRuleViewSet(HWMModelViewSet):
    queryset = RamadanComplianceRule.objects.select_related("compliance_config")
    serializer_class = RamadanComplianceRuleSerializer
    filterset_fields = ["compliance_config"]
    ordering_fields = ["created_at"]


class WardRatioConfigViewSet(HWMModelViewSet):
    queryset = WardRatioConfig.objects.select_related("compliance_config")
    serializer_class = WardRatioConfigSerializer
    filterset_fields = ["compliance_config", "ward_type"]
    ordering_fields = ["ward_type", "created_at"]


class ComplianceAuditLogViewSet(HWMModelViewSet):
    queryset = ComplianceAuditLog.objects.all()
    serializer_class = ComplianceAuditLogSerializer
    filterset_fields = ["actor_user_id", "action", "resource_type"]
    ordering_fields = ["created_at"]
    http_method_names = ["get", "post", "head", "options"]
