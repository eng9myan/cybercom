from rest_framework import viewsets
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from .models import PriceList, ServicePrice, PackagePrice, DiscountRule
from .serializers import (
    PriceListSerializer, ServicePriceSerializer,
    PackagePriceSerializer, DiscountRuleSerializer,
)


class PriceListViewSet(viewsets.ModelViewSet):
    queryset = PriceList.objects.all()
    serializer_class = PriceListSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["facility_id", "service_category", "is_active", "is_default", "currency"]
    search_fields = ["list_name", "list_code"]
    ordering = ["-effective_date"]

    def get_queryset(self):
        tenant_id = self.request.headers.get("X-Tenant-ID")
        if tenant_id:
            return self.queryset.filter(tenant_id=tenant_id)
        return self.queryset


class ServicePriceViewSet(viewsets.ModelViewSet):
    queryset = ServicePrice.objects.all()
    serializer_class = ServicePriceSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["price_list", "service_category", "is_active"]
    search_fields = ["service_code", "service_description"]
    ordering = ["service_code"]

    def get_queryset(self):
        tenant_id = self.request.headers.get("X-Tenant-ID")
        if tenant_id:
            return self.queryset.filter(tenant_id=tenant_id)
        return self.queryset


class PackagePriceViewSet(viewsets.ModelViewSet):
    queryset = PackagePrice.objects.all()
    serializer_class = PackagePriceSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["price_list", "package_type", "is_active"]
    search_fields = ["package_name", "package_code"]
    ordering = ["package_name"]

    def get_queryset(self):
        tenant_id = self.request.headers.get("X-Tenant-ID")
        if tenant_id:
            return self.queryset.filter(tenant_id=tenant_id)
        return self.queryset


class DiscountRuleViewSet(viewsets.ModelViewSet):
    queryset = DiscountRule.objects.all()
    serializer_class = DiscountRuleSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["discount_type", "applies_to", "is_active"]
    search_fields = ["rule_name"]
    ordering = ["rule_name"]

    def get_queryset(self):
        tenant_id = self.request.headers.get("X-Tenant-ID")
        if tenant_id:
            return self.queryset.filter(tenant_id=tenant_id)
        return self.queryset
