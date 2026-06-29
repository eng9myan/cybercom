from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions, viewsets

from .models import (
    ApprovalAuditLog,
    ApprovalDecision,
    ApprovalRequest,
    ApprovalWorkflow,
)
from .serializers import (
    ApprovalAuditLogSerializer,
    ApprovalDecisionSerializer,
    ApprovalRequestSerializer,
    ApprovalWorkflowSerializer,
)


class ApprovalRequestViewSet(viewsets.ModelViewSet):
    serializer_class = ApprovalRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = [
        "approval_type",
        "requested_by_provider_id",
        "approver_id",
        "patient_id",
        "priority",
        "status",
        "reference_type",
    ]
    search_fields = [
        "title",
        "description",
        "requested_by_name",
        "approver_name",
        "rejection_reason",
    ]
    ordering_fields = ["created_at", "due_by", "decided_at", "priority", "status"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return ApprovalRequest.objects.filter(tenant_id=self.request.tenant_id).prefetch_related(
            "decisions", "audit_log"
        )


class ApprovalWorkflowViewSet(viewsets.ModelViewSet):
    serializer_class = ApprovalWorkflowSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = [
        "approval_type",
        "is_sequential",
        "requires_all_approvers",
        "is_active",
        "created_by_provider_id",
        "specialty",
    ]
    search_fields = ["workflow_name", "approval_type", "specialty"]
    ordering_fields = ["created_at", "workflow_name", "approval_type"]
    ordering = ["workflow_name"]

    def get_queryset(self):
        return ApprovalWorkflow.objects.filter(tenant_id=self.request.tenant_id)


class ApprovalDecisionViewSet(viewsets.ModelViewSet):
    serializer_class = ApprovalDecisionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["approval_request", "decided_by_provider_id", "decision", "step_order"]
    search_fields = ["decided_by_name", "decision_notes", "conditions"]
    ordering_fields = ["created_at", "decision", "step_order"]
    ordering = ["step_order", "-created_at"]

    def get_queryset(self):
        return ApprovalDecision.objects.filter(tenant_id=self.request.tenant_id)


class ApprovalAuditLogViewSet(viewsets.ModelViewSet):
    serializer_class = ApprovalAuditLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["approval_request", "action", "performed_by_provider_id"]
    search_fields = ["performed_by_name", "action", "ip_address"]
    ordering_fields = ["created_at", "action"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return ApprovalAuditLog.objects.filter(tenant_id=self.request.tenant_id)
