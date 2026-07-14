from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.filters import OrderingFilter, SearchFilter

from .models import (
    MobilePreferences,
    MobilePushNotification,
    MobileSession,
    ProviderMobileDevice,
)
from .serializers import (
    MobilePreferencesSerializer,
    MobilePushNotificationSerializer,
    MobileSessionSerializer,
    ProviderMobileDeviceSerializer,
)


class ProviderMobileDeviceViewSet(viewsets.ModelViewSet):
    serializer_class = ProviderMobileDeviceSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = [
        "provider_id",
        "device_type",
        "is_active",
        "is_trusted",
        "provider_workspace_id",
    ]
    search_fields = ["device_name", "platform_version", "app_version"]
    ordering_fields = ["registered_at", "last_used_at", "created_at"]
    ordering = ["-registered_at"]

    def get_queryset(self):
        return ProviderMobileDevice.objects.filter(tenant_id=self.request.tenant_id)


class MobileSessionViewSet(viewsets.ModelViewSet):
    serializer_class = MobileSessionSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = [
        "provider_id",
        "device",
        "is_active",
        "biometric_verified",
        "context_patient_id",
    ]
    search_fields = ["session_token", "ip_address"]
    ordering_fields = ["started_at", "ended_at", "created_at"]
    ordering = ["-started_at"]

    def get_queryset(self):
        return MobileSession.objects.filter(tenant_id=self.request.tenant_id)


class MobilePreferencesViewSet(viewsets.ModelViewSet):
    serializer_class = MobilePreferencesSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = [
        "provider_id",
        "device",
        "home_tab",
        "biometric_login",
        "push_critical_results",
    ]
    search_fields = ["quick_action_1", "quick_action_2"]
    ordering_fields = ["created_at", "updated_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return MobilePreferences.objects.filter(tenant_id=self.request.tenant_id)


class MobilePushNotificationViewSet(viewsets.ModelViewSet):
    serializer_class = MobilePushNotificationSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = [
        "provider_id",
        "device_id",
        "notification_type",
        "priority",
        "is_delivered",
        "is_read",
    ]
    search_fields = ["title", "body", "action_type", "source_type"]
    ordering_fields = ["created_at", "delivered_at", "read_at", "priority"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return MobilePushNotification.objects.filter(tenant_id=self.request.tenant_id)
