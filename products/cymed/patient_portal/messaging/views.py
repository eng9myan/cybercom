from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions, viewsets

from .models import MessageAttachment, MessageThread, PatientMessage, SecureMessageRecipient
from .serializers import (
    MessageAttachmentSerializer,
    MessageThreadDetailSerializer,
    MessageThreadSerializer,
    PatientMessageSerializer,
    SecureMessageRecipientSerializer,
)


class MessageThreadViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["status", "thread_type", "is_urgent"]
    search_fields = ["subject", "provider_name", "facility_name"]
    ordering_fields = ["created_at", "last_message_at"]
    ordering = ["-last_message_at"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return MessageThreadDetailSerializer
        return MessageThreadSerializer

    def get_queryset(self):
        return MessageThread.objects.filter(
            tenant_id=self.request.tenant_id,
            account_id=self.request.account_id,
        )


class PatientMessageViewSet(viewsets.ModelViewSet):
    serializer_class = PatientMessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["thread", "sender_type", "is_read", "is_system_message"]
    ordering_fields = ["sent_at"]
    ordering = ["-sent_at"]

    def get_queryset(self):
        return PatientMessage.objects.filter(
            tenant_id=self.request.tenant_id,
            account_id=self.request.account_id,
        )


class MessageAttachmentViewSet(viewsets.ModelViewSet):
    serializer_class = MessageAttachmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["message", "file_type"]
    ordering_fields = ["uploaded_at"]
    ordering = ["-uploaded_at"]

    def get_queryset(self):
        return MessageAttachment.objects.filter(
            tenant_id=self.request.tenant_id,
            account_id=self.request.account_id,
        )


class SecureMessageRecipientViewSet(viewsets.ModelViewSet):
    serializer_class = SecureMessageRecipientSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["thread", "recipient_type", "is_active"]
    ordering_fields = ["added_at"]
    ordering = ["-added_at"]

    def get_queryset(self):
        return SecureMessageRecipient.objects.filter(
            tenant_id=self.request.tenant_id,
        )
