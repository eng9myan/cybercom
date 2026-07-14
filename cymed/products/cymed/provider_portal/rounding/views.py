from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated

from products.cymed.provider_portal.rounding.models import (
    ClinicalRound,
    RoundAction,
    RoundChecklist,
    RoundFinding,
    RoundTeam,
)
from products.cymed.provider_portal.rounding.serializers import (
    ClinicalRoundSerializer,
    RoundActionSerializer,
    RoundChecklistSerializer,
    RoundFindingSerializer,
    RoundTeamSerializer,
)


class ClinicalRoundViewSet(viewsets.ModelViewSet):
    queryset = ClinicalRound.objects.all()
    serializer_class = ClinicalRoundSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["round_type", "unit_id", "attending_provider_id", "round_date", "status"]
    search_fields = ["round_name", "attending_name", "unit_name", "notes"]
    ordering_fields = ["round_date", "scheduled_time", "created_at"]
    ordering = ["-round_date"]

    def get_queryset(self):
        tenant_id = getattr(self.request, "tenant_id", None)
        if tenant_id:
            return self.queryset.filter(tenant_id=tenant_id)
        return self.queryset.none()


class RoundTeamViewSet(viewsets.ModelViewSet):
    queryset = RoundTeam.objects.all()
    serializer_class = RoundTeamSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["round", "provider_id", "role", "is_present"]
    search_fields = ["provider_name", "provider_type"]
    ordering_fields = ["created_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        tenant_id = getattr(self.request, "tenant_id", None)
        if tenant_id:
            return self.queryset.filter(tenant_id=tenant_id)
        return self.queryset.none()


class RoundChecklistViewSet(viewsets.ModelViewSet):
    queryset = RoundChecklist.objects.all()
    serializer_class = RoundChecklistSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["round", "patient_id"]
    search_fields = ["patient_name", "bed_number"]
    ordering_fields = ["created_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        tenant_id = getattr(self.request, "tenant_id", None)
        if tenant_id:
            return self.queryset.filter(tenant_id=tenant_id)
        return self.queryset.none()


class RoundFindingViewSet(viewsets.ModelViewSet):
    queryset = RoundFinding.objects.all()
    serializer_class = RoundFindingSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = [
        "round",
        "patient_id",
        "finding_type",
        "severity",
        "requires_action",
        "is_resolved",
    ]
    search_fields = ["finding_text", "recorded_by_name"]
    ordering_fields = ["created_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        tenant_id = getattr(self.request, "tenant_id", None)
        if tenant_id:
            return self.queryset.filter(tenant_id=tenant_id)
        return self.queryset.none()


class RoundActionViewSet(viewsets.ModelViewSet):
    queryset = RoundAction.objects.all()
    serializer_class = RoundActionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["round", "finding", "patient_id", "action_type", "status"]
    search_fields = ["action_description", "assigned_to_name"]
    ordering_fields = ["due_by", "created_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        tenant_id = getattr(self.request, "tenant_id", None)
        if tenant_id:
            return self.queryset.filter(tenant_id=tenant_id)
        return self.queryset.none()
