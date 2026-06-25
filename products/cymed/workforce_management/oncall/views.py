from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import OnCallRoster, OnCallAssignment, OnCallPage, OnCallEscalation, CallSwapRequest
from .serializers import (
    OnCallRosterSerializer,
    OnCallAssignmentSerializer,
    OnCallPageSerializer,
    OnCallEscalationSerializer,
    CallSwapRequestSerializer,
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


class OnCallRosterViewSet(HWMModelViewSet):
    queryset = OnCallRoster.objects.all()
    serializer_class = OnCallRosterSerializer
    filterset_fields = ["facility_id", "department_id", "specialty", "roster_date", "status"]
    search_fields = ["specialty"]
    ordering_fields = ["roster_date", "status", "created_at"]

    @action(detail=True, methods=["post"])
    def publish(self, request, pk=None):
        roster = self.get_object()
        roster.status = "published"
        roster.published_by_id = request.user.id if hasattr(request, "user") else None
        roster.published_at = timezone.now()
        roster.save(update_fields=["status", "published_by_id", "published_at", "updated_at"])
        return Response({"status": "published", "id": str(roster.id)})

    @action(detail=True, methods=["get"])
    def assignments(self, request, pk=None):
        roster = self.get_object()
        qs = roster.assignments.all()
        serializer = OnCallAssignmentSerializer(qs, many=True)
        return Response(serializer.data)


class OnCallAssignmentViewSet(HWMModelViewSet):
    queryset = OnCallAssignment.objects.select_related("oncall_roster")
    serializer_class = OnCallAssignmentSerializer
    filterset_fields = ["oncall_roster", "workforce_profile_id", "call_mode", "call_tier", "call_seniority", "is_active"]
    ordering_fields = ["created_at"]


class OnCallPageViewSet(HWMModelViewSet):
    queryset = OnCallPage.objects.select_related("oncall_roster")
    serializer_class = OnCallPageSerializer
    filterset_fields = ["oncall_roster", "initiating_ward_id", "urgency", "status"]
    ordering_fields = ["triggered_at", "urgency", "created_at"]

    @action(detail=True, methods=["post"])
    def acknowledge(self, request, pk=None):
        page = self.get_object()
        page.status = "acknowledged"
        page.acknowledged_at = timezone.now()
        page.save(update_fields=["status", "acknowledged_at", "updated_at"])
        return Response({"status": "acknowledged", "id": str(page.id)})

    @action(detail=True, methods=["post"])
    def resolve(self, request, pk=None):
        page = self.get_object()
        page.status = "resolved"
        page.resolved_at = timezone.now()
        page.resolved_by_id = request.data.get("resolved_by_id")
        page.save(update_fields=["status", "resolved_at", "resolved_by_id", "updated_at"])
        return Response({"status": "resolved", "id": str(page.id)})

    @action(detail=True, methods=["get"])
    def escalations(self, request, pk=None):
        page = self.get_object()
        qs = page.escalations.all()
        serializer = OnCallEscalationSerializer(qs, many=True)
        return Response(serializer.data)


class OnCallEscalationViewSet(HWMModelViewSet):
    queryset = OnCallEscalation.objects.select_related("page")
    serializer_class = OnCallEscalationSerializer
    filterset_fields = ["page", "escalation_level", "escalated_to_profile_id", "department_chair_alerted"]
    ordering_fields = ["triggered_at", "escalation_level", "created_at"]
    http_method_names = ["get", "post", "head", "options"]

    @action(detail=True, methods=["post"])
    def acknowledge(self, request, pk=None):
        escalation = self.get_object()
        escalation.acknowledged_at = timezone.now()
        escalation.save(update_fields=["acknowledged_at", "updated_at"])
        return Response({"status": "acknowledged", "id": str(escalation.id)})


class CallSwapRequestViewSet(HWMModelViewSet):
    queryset = CallSwapRequest.objects.select_related("original_assignment")
    serializer_class = CallSwapRequestSerializer
    filterset_fields = ["original_assignment", "requester_profile_id", "recipient_profile_id", "status"]
    ordering_fields = ["created_at"]

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        swap = self.get_object()
        swap.status = "approved"
        swap.approver_id = request.data.get("approver_id")
        swap.approver_role = request.data.get("approver_role", "")
        swap.approved_at = timezone.now()
        swap.save(update_fields=["status", "approver_id", "approver_role", "approved_at", "updated_at"])
        return Response({"status": "approved", "id": str(swap.id)})

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        swap = self.get_object()
        swap.status = "rejected"
        swap.save(update_fields=["status", "updated_at"])
        return Response({"status": "rejected", "id": str(swap.id)})
