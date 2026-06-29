from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated

from products.cymed.provider_portal.clinical_messaging.models import (
    ClinicalGroup,
    ClinicalMessage,
    ClinicalMessageThread,
    MessageAttachment,
    MessageThreadParticipant,
)
from products.cymed.provider_portal.clinical_messaging.serializers import (
    ClinicalGroupSerializer,
    ClinicalMessageSerializer,
    ClinicalMessageThreadSerializer,
    MessageAttachmentSerializer,
    MessageThreadParticipantSerializer,
)


class ClinicalMessageThreadViewSet(viewsets.ModelViewSet):
    queryset = ClinicalMessageThread.objects.all()
    serializer_class = ClinicalMessageThreadSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = [
        "thread_type",
        "status",
        "is_urgent",
        "patient_id",
        "created_by_provider_id",
    ]
    search_fields = ["subject"]
    ordering_fields = ["last_message_at", "created_at"]
    ordering = ["-last_message_at"]

    def get_queryset(self):
        return self.queryset.filter(tenant_id=self.request.tenant_id)


class ClinicalMessageViewSet(viewsets.ModelViewSet):
    queryset = ClinicalMessage.objects.all()
    serializer_class = ClinicalMessageSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = [
        "thread",
        "sender_provider_id",
        "is_read",
        "priority",
        "is_system_message",
    ]
    search_fields = ["body", "sender_name"]
    ordering_fields = ["sent_at"]
    ordering = ["-sent_at"]

    def get_queryset(self):
        return self.queryset.filter(tenant_id=self.request.tenant_id)


class MessageAttachmentViewSet(viewsets.ModelViewSet):
    queryset = MessageAttachment.objects.all()
    serializer_class = MessageAttachmentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["message", "attachment_type", "file_type"]
    search_fields = ["file_name", "description"]
    ordering_fields = ["created_at", "file_size_bytes"]
    ordering = ["created_at"]

    def get_queryset(self):
        return self.queryset.filter(tenant_id=self.request.tenant_id)


class ClinicalGroupViewSet(viewsets.ModelViewSet):
    queryset = ClinicalGroup.objects.all()
    serializer_class = ClinicalGroupSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["group_type", "is_active", "admin_provider_id"]
    search_fields = ["name", "description"]
    ordering_fields = ["name", "created_at"]
    ordering = ["name"]

    def get_queryset(self):
        return self.queryset.filter(tenant_id=self.request.tenant_id)


class MessageThreadParticipantViewSet(viewsets.ModelViewSet):
    queryset = MessageThreadParticipant.objects.all()
    serializer_class = MessageThreadParticipantSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["thread", "provider_id", "is_active", "provider_type"]
    search_fields = ["provider_name"]
    ordering_fields = ["joined_at", "last_read_at"]
    ordering = ["joined_at"]

    def get_queryset(self):
        return self.queryset.filter(tenant_id=self.request.tenant_id)
