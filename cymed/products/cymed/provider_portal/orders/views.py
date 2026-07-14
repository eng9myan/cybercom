from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated

from products.cymed.provider_portal.orders.models import (
    OrderModification,
    OrderSet,
    OrderStatusUpdate,
    ProviderOrderRequest,
)
from products.cymed.provider_portal.orders.serializers import (
    OrderModificationSerializer,
    OrderSetSerializer,
    OrderStatusUpdateSerializer,
    ProviderOrderRequestSerializer,
)


class ProviderOrderRequestViewSet(viewsets.ModelViewSet):
    queryset = ProviderOrderRequest.objects.all()
    serializer_class = ProviderOrderRequestSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = [
        "patient_id",
        "ordering_provider_id",
        "order_category",
        "priority",
        "status",
        "cymed_encounter_id",
    ]
    search_fields = ["order_name", "order_type", "ordering_provider_name", "clinical_indication"]
    ordering_fields = ["submitted_at", "created_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        tenant_id = getattr(self.request, "tenant_id", None)
        if tenant_id:
            return self.queryset.filter(tenant_id=tenant_id)
        return self.queryset.none()


class OrderModificationViewSet(viewsets.ModelViewSet):
    queryset = OrderModification.objects.all()
    serializer_class = OrderModificationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["order", "modification_type", "is_applied"]
    search_fields = ["modified_by_name", "reason"]
    ordering_fields = ["created_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        tenant_id = getattr(self.request, "tenant_id", None)
        if tenant_id:
            return self.queryset.filter(tenant_id=tenant_id)
        return self.queryset.none()


class OrderStatusUpdateViewSet(viewsets.ModelViewSet):
    queryset = OrderStatusUpdate.objects.all()
    serializer_class = OrderStatusUpdateSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["order", "previous_status", "new_status"]
    search_fields = ["updated_by_name", "updated_by_system", "notes"]
    ordering_fields = ["created_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        tenant_id = getattr(self.request, "tenant_id", None)
        if tenant_id:
            return self.queryset.filter(tenant_id=tenant_id)
        return self.queryset.none()


class OrderSetViewSet(viewsets.ModelViewSet):
    queryset = OrderSet.objects.all()
    serializer_class = OrderSetSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = [
        "order_set_type",
        "specialty",
        "created_by_provider_id",
        "is_shared",
        "is_active",
    ]
    search_fields = ["name", "description", "specialty"]
    ordering_fields = ["name", "usage_count", "created_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        tenant_id = getattr(self.request, "tenant_id", None)
        if tenant_id:
            return self.queryset.filter(tenant_id=tenant_id)
        return self.queryset.none()
