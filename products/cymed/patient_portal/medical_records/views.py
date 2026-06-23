from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .models import (
    MedicalRecordAccess,
    SharedRecord,
    RecordDownloadHistory,
    PatientDocument,
)
from .serializers import (
    MedicalRecordAccessSerializer,
    SharedRecordSerializer,
    RecordDownloadHistorySerializer,
    PatientDocumentSerializer,
)


class MedicalRecordAccessViewSet(viewsets.ModelViewSet):
    serializer_class = MedicalRecordAccessSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['account_id', 'patient_id', 'record_type', 'access_type']
    ordering_fields = ['accessed_at', 'created_at']
    ordering = ['-accessed_at']

    def get_queryset(self):
        return MedicalRecordAccess.objects.filter(tenant_id=self.request.tenant_id)


class SharedRecordViewSet(viewsets.ModelViewSet):
    serializer_class = SharedRecordSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['account_id', 'patient_id', 'shared_with_type', 'is_revoked', 'record_type']
    search_fields = ['record_title', 'shared_with_name', 'shared_with_email']
    ordering_fields = ['created_at', 'valid_until', 'access_count']
    ordering = ['-created_at']

    def get_queryset(self):
        return SharedRecord.objects.filter(tenant_id=self.request.tenant_id)

    @action(detail=True, methods=['post'], url_path='revoke')
    def revoke(self, request, pk=None):
        from django.utils import timezone
        record = self.get_object()
        if record.is_revoked:
            return Response(
                {'detail': 'This shared record has already been revoked.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        record.is_revoked = True
        record.revoked_at = timezone.now()
        record.save(update_fields=['is_revoked', 'revoked_at', 'updated_at'])
        serializer = SharedRecordSerializer(record)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='increment-access')
    def increment_access(self, request, pk=None):
        record = self.get_object()
        if record.is_revoked:
            return Response(
                {'detail': 'This shared record has been revoked.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        if record.max_access_count and record.access_count >= record.max_access_count:
            return Response(
                {'detail': 'Maximum access count reached for this shared record.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        record.access_count += 1
        record.save(update_fields=['access_count', 'updated_at'])
        serializer = SharedRecordSerializer(record)
        return Response(serializer.data)


class RecordDownloadHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = RecordDownloadHistorySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['account_id', 'patient_id', 'record_type', 'download_format']
    ordering_fields = ['downloaded_at', 'created_at']
    ordering = ['-downloaded_at']

    def get_queryset(self):
        return RecordDownloadHistory.objects.filter(tenant_id=self.request.tenant_id)


class PatientDocumentViewSet(viewsets.ModelViewSet):
    serializer_class = PatientDocumentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['account_id', 'patient_id', 'document_type', 'source', 'is_shared']
    search_fields = ['title', 'description', 'provider_name', 'file_name']
    ordering_fields = ['created_at', 'document_date', 'title']
    ordering = ['-created_at']

    def get_queryset(self):
        return PatientDocument.objects.filter(tenant_id=self.request.tenant_id)

    @action(detail=True, methods=['post'], url_path='toggle-share')
    def toggle_share(self, request, pk=None):
        document = self.get_object()
        document.is_shared = not document.is_shared
        document.save(update_fields=['is_shared', 'updated_at'])
        serializer = PatientDocumentSerializer(document)
        return Response(serializer.data)
