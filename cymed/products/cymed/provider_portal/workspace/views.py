from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated

from products.cymed.provider_portal.workspace.models import (
    ProviderDashboard,
    ProviderPreferences,
    ProviderWorkspace,
    WorkspaceSession,
)
from products.cymed.provider_portal.workspace.serializers import (
    ProviderDashboardSerializer,
    ProviderPreferencesSerializer,
    ProviderWorkspaceSerializer,
    WorkspaceSessionSerializer,
)


class ProviderWorkspaceViewSet(viewsets.ModelViewSet):
    queryset = ProviderWorkspace.objects.all()
    serializer_class = ProviderWorkspaceSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["provider_type", "is_active", "department"]
    search_fields = ["preferred_specialty", "home_unit_name", "department"]
    ordering_fields = ["created_at", "last_active_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return self.queryset.filter(tenant_id=self.request.tenant_id)


class ProviderDashboardViewSet(viewsets.ModelViewSet):
    queryset = ProviderDashboard.objects.all()
    serializer_class = ProviderDashboardSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["workspace"]
    ordering_fields = ["created_at", "updated_at"]
    ordering = ["-updated_at"]

    def get_queryset(self):
        return self.queryset.filter(tenant_id=self.request.tenant_id)


class ProviderPreferencesViewSet(viewsets.ModelViewSet):
    queryset = ProviderPreferences.objects.all()
    serializer_class = ProviderPreferencesSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["workspace", "ai_suggestions_enabled", "voice_dictation_enabled"]
    ordering_fields = ["created_at", "updated_at"]
    ordering = ["-updated_at"]

    def get_queryset(self):
        return self.queryset.filter(tenant_id=self.request.tenant_id)


class WorkspaceSessionViewSet(viewsets.ModelViewSet):
    queryset = WorkspaceSession.objects.all()
    serializer_class = WorkspaceSessionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["workspace", "device_type", "is_active"]
    search_fields = ["ip_address", "user_agent"]
    ordering_fields = ["started_at", "ended_at"]
    ordering = ["-started_at"]

    def get_queryset(self):
        return self.queryset.filter(tenant_id=self.request.tenant_id)
