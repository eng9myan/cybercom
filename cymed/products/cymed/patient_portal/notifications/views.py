from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions, viewsets

from .models import (
    NotificationPreference,
    NotificationTemplate,
    PatientNotification,
    PushSubscription,
)
from .serializers import (
    NotificationPreferenceSerializer,
    NotificationTemplateSerializer,
    PatientNotificationSerializer,
    PushSubscriptionSerializer,
)


class PatientNotificationViewSet(viewsets.ModelViewSet):
    serializer_class = PatientNotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["notification_type", "priority", "is_read", "is_dismissed"]
    ordering_fields = ["created_at", "priority", "expires_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return PatientNotification.objects.filter(
            tenant_id=self.request.tenant_id,
            account_id=self.request.account_id,
        )


class NotificationPreferenceViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationPreferenceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return NotificationPreference.objects.filter(
            tenant_id=self.request.tenant_id,
            account_id=self.request.account_id,
        )


class NotificationTemplateViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationTemplateSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["notification_type", "channel", "language", "is_active"]
    ordering_fields = ["created_at", "code"]
    ordering = ["code"]

    def get_queryset(self):
        return NotificationTemplate.objects.filter(
            tenant_id=self.request.tenant_id,
        )


class PushSubscriptionViewSet(viewsets.ModelViewSet):
    serializer_class = PushSubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["platform", "is_active"]
    ordering_fields = ["created_at", "last_used_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return PushSubscription.objects.filter(
            tenant_id=self.request.tenant_id,
            account_id=self.request.account_id,
        )
