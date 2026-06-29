from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions, viewsets

from .models import (
    ConsultRequest,
    ProviderTelemedicineSession,
    SecondOpinionRequest,
    TelemedicineDocument,
)
from .serializers import (
    ConsultRequestSerializer,
    ProviderTelemedicineSessionSerializer,
    SecondOpinionRequestSerializer,
    TelemedicineDocumentSerializer,
)


class ProviderTelemedicineSessionViewSet(viewsets.ModelViewSet):
    serializer_class = ProviderTelemedicineSessionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = [
        "patient_id",
        "provider_id",
        "session_type",
        "visit_type",
        "status",
        "cymed_encounter_id",
        "follow_up_required",
    ]
    search_fields = ["provider_name", "provider_type", "session_summary", "meeting_id"]
    ordering_fields = ["created_at", "scheduled_at", "status", "duration_minutes"]
    ordering = ["-scheduled_at"]

    def get_queryset(self):
        return ProviderTelemedicineSession.objects.filter(
            tenant_id=self.request.tenant_id
        ).prefetch_related("documents")


class ConsultRequestViewSet(viewsets.ModelViewSet):
    serializer_class = ConsultRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = [
        "patient_id",
        "requesting_provider_id",
        "consulting_provider_id",
        "consulting_specialty",
        "urgency",
        "status",
        "is_telemedicine",
    ]
    search_fields = [
        "consulting_specialty",
        "consult_reason",
        "requesting_provider_name",
        "response_summary",
    ]
    ordering_fields = ["created_at", "urgency", "status", "accepted_at", "completed_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return ConsultRequest.objects.filter(tenant_id=self.request.tenant_id)


class SecondOpinionRequestViewSet(viewsets.ModelViewSet):
    serializer_class = SecondOpinionRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = [
        "patient_id",
        "requesting_provider_id",
        "requested_specialist_id",
        "requested_specialty",
        "urgency",
        "status",
    ]
    search_fields = ["requested_specialty", "clinical_question", "opinion_text"]
    ordering_fields = ["created_at", "urgency", "status", "completed_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return SecondOpinionRequest.objects.filter(tenant_id=self.request.tenant_id)


class TelemedicineDocumentViewSet(viewsets.ModelViewSet):
    serializer_class = TelemedicineDocumentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["session", "document_type", "uploaded_by", "file_type"]
    search_fields = ["file_name", "description", "document_type"]
    ordering_fields = ["created_at", "file_size_bytes", "document_type"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return TelemedicineDocument.objects.filter(tenant_id=self.request.tenant_id)
