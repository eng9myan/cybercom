from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import ShiftSwapApproval, ShiftSwapRequest, SwapValidationLog
from .serializers import (
    ShiftSwapApprovalSerializer,
    ShiftSwapRequestSerializer,
    SwapValidationLogSerializer,
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


class ShiftSwapRequestViewSet(HWMModelViewSet):
    queryset = ShiftSwapRequest.objects.all()
    serializer_class = ShiftSwapRequestSerializer
    filterset_fields = ["requester_profile_id", "recipient_profile_id", "status"]
    ordering_fields = ["proposed_at", "status", "created_at"]

    @action(detail=True, methods=["post"])
    def accept(self, request, pk=None):
        swap = self.get_object()
        swap.status = "pending_validation"
        swap.recipient_responded_at = timezone.now()
        swap.save(update_fields=["status", "recipient_responded_at", "updated_at"])
        return Response({"status": "pending_validation", "id": str(swap.id)})

    @action(detail=True, methods=["post"])
    def decline(self, request, pk=None):
        swap = self.get_object()
        swap.status = "rejected"
        swap.rejection_reason = "recipient_declined"
        swap.recipient_responded_at = timezone.now()
        swap.save(
            update_fields=["status", "rejection_reason", "recipient_responded_at", "updated_at"]
        )
        return Response({"status": "rejected", "id": str(swap.id)})

    @action(detail=True, methods=["post"])
    def commit(self, request, pk=None):
        swap = self.get_object()
        swap.status = "committed"
        swap.committed_at = timezone.now()
        swap.save(update_fields=["status", "committed_at", "updated_at"])
        return Response({"status": "committed", "id": str(swap.id)})

    @action(detail=True, methods=["get"])
    def validations(self, request, pk=None):
        swap = self.get_object()
        qs = swap.validation_logs.all()
        serializer = SwapValidationLogSerializer(qs, many=True)
        return Response(serializer.data)


class ShiftSwapApprovalViewSet(HWMModelViewSet):
    queryset = ShiftSwapApproval.objects.select_related("swap_request")
    serializer_class = ShiftSwapApprovalSerializer
    filterset_fields = ["swap_request", "decision", "approver_id"]
    ordering_fields = ["decided_at", "created_at"]
    http_method_names = ["get", "post", "head", "options"]


class SwapValidationLogViewSet(HWMModelViewSet):
    queryset = SwapValidationLog.objects.select_related("swap_request")
    serializer_class = SwapValidationLogSerializer
    filterset_fields = ["swap_request", "check_type", "passed"]
    ordering_fields = ["checked_at", "created_at"]
    http_method_names = ["get", "head", "options"]
