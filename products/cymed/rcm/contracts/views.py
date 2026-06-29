from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response

from .models import ContractRate, ContractRule, PayerContract, ReimbursementRule
from .serializers import (
    ContractRateSerializer,
    ContractRuleSerializer,
    PayerContractSerializer,
    ReimbursementRuleSerializer,
)


class PayerContractViewSet(viewsets.ModelViewSet):
    queryset = PayerContract.objects.all()
    serializer_class = PayerContractSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["insurance_company_id", "status", "contract_type", "facility_id"]
    search_fields = ["contract_name", "contract_number"]
    ordering_fields = ["effective_date", "status"]
    ordering = ["-effective_date"]

    def get_queryset(self):
        tenant_id = self.request.headers.get("X-Tenant-ID")
        if tenant_id:
            return self.queryset.filter(tenant_id=tenant_id)
        return self.queryset

    @action(detail=True, methods=["post"])
    def renew(self, request, pk=None):
        contract = self.get_object()
        contract.status = "pending_renewal"
        contract.save()
        return Response({"status": "pending_renewal", "id": str(contract.id)})


class ContractRateViewSet(viewsets.ModelViewSet):
    queryset = ContractRate.objects.all()
    serializer_class = ContractRateSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["contract", "rate_type", "is_active"]
    search_fields = ["service_code", "service_description"]
    ordering = ["service_code"]

    def get_queryset(self):
        tenant_id = self.request.headers.get("X-Tenant-ID")
        if tenant_id:
            return self.queryset.filter(tenant_id=tenant_id)
        return self.queryset


class ContractRuleViewSet(viewsets.ModelViewSet):
    queryset = ContractRule.objects.all()
    serializer_class = ContractRuleSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["contract", "rule_type", "is_active"]
    ordering = ["rule_type"]

    def get_queryset(self):
        tenant_id = self.request.headers.get("X-Tenant-ID")
        if tenant_id:
            return self.queryset.filter(tenant_id=tenant_id)
        return self.queryset


class ReimbursementRuleViewSet(viewsets.ModelViewSet):
    queryset = ReimbursementRule.objects.all()
    serializer_class = ReimbursementRuleSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["contract", "calculation_method", "is_active"]
    ordering = ["rule_name"]

    def get_queryset(self):
        tenant_id = self.request.headers.get("X-Tenant-ID")
        if tenant_id:
            return self.queryset.filter(tenant_id=tenant_id)
        return self.queryset
