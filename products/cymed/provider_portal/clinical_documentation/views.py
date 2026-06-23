from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend

from .models import (
    DocumentationTemplate,
    SmartPhrase,
    ProviderClinicalNote,
    NoteCoSignature,
    VoiceDictation,
)
from .serializers import (
    DocumentationTemplateSerializer,
    SmartPhraseSerializer,
    ProviderClinicalNoteSerializer,
    NoteCoSignatureSerializer,
    VoiceDictationSerializer,
)


class DocumentationTemplateViewSet(viewsets.ModelViewSet):
    serializer_class = DocumentationTemplateSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['template_type', 'specialty', 'is_shared', 'is_active', 'created_by_provider_id']
    search_fields = ['name', 'specialty', 'content_template']
    ordering_fields = ['created_at', 'name', 'usage_count', 'template_type']
    ordering = ['-created_at']

    def get_queryset(self):
        return DocumentationTemplate.objects.filter(tenant_id=self.request.tenant_id)


class SmartPhraseViewSet(viewsets.ModelViewSet):
    serializer_class = SmartPhraseSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['phrase_type', 'is_personal', 'specialty', 'is_active', 'created_by_provider_id']
    search_fields = ['code', 'expansion', 'specialty']
    ordering_fields = ['created_at', 'code', 'phrase_type']
    ordering = ['code']

    def get_queryset(self):
        return SmartPhrase.objects.filter(tenant_id=self.request.tenant_id)


class ProviderClinicalNoteViewSet(viewsets.ModelViewSet):
    serializer_class = ProviderClinicalNoteSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['patient_id', 'author_provider_id', 'note_type', 'status', 'is_confidential', 'cymed_encounter_id']
    search_fields = ['note_title', 'note_body', 'author_name', 'author_type']
    ordering_fields = ['created_at', 'signed_at', 'status', 'note_type']
    ordering = ['-created_at']

    def get_queryset(self):
        return ProviderClinicalNote.objects.filter(
            tenant_id=self.request.tenant_id
        ).prefetch_related('cosignatures', 'dictations')


class NoteCoSignatureViewSet(viewsets.ModelViewSet):
    serializer_class = NoteCoSignatureSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['note', 'cosigner_provider_id', 'role', 'is_signed']
    search_fields = ['cosigner_name', 'cosigner_type', 'rejection_reason']
    ordering_fields = ['created_at', 'requested_at', 'signed_at']
    ordering = ['-created_at']

    def get_queryset(self):
        return NoteCoSignature.objects.filter(tenant_id=self.request.tenant_id)


class VoiceDictationViewSet(viewsets.ModelViewSet):
    serializer_class = VoiceDictationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['note', 'provider_id', 'status', 'integration_provider']
    search_fields = ['transcript_text', 'ai_transcript', 'integration_provider']
    ordering_fields = ['created_at', 'status', 'duration_seconds']
    ordering = ['-created_at']

    def get_queryset(self):
        return VoiceDictation.objects.filter(tenant_id=self.request.tenant_id)
