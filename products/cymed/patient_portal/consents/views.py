from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone

from .models import (
    PortalConsentType,
    PortalConsentRecord,
    ConsentRequest,
    ConsentHistory,
)
from .serializers import (
    PortalConsentTypeSerializer,
    PortalConsentRecordSerializer,
    PortalConsentRecordWriteSerializer,
    ConsentRequestSerializer,
    ConsentHistorySerializer,
)


class PortalConsentTypeViewSet(viewsets.ModelViewSet):
    serializer_class = PortalConsentTypeSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['consent_category', 'is_mandatory', 'is_active']
    search_fields = ['code', 'name', 'name_ar', 'description']
    ordering_fields = ['consent_category', 'name', 'created_at']
    ordering = ['consent_category', 'name']

    def get_queryset(self):
        return PortalConsentType.objects.filter(tenant_id=self.request.tenant_id)

    @action(detail=False, methods=['get'], url_path='active')
    def active_types(self, request):
        queryset = self.get_queryset().filter(is_active=True)
        serializer = PortalConsentTypeSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='mandatory')
    def mandatory_types(self, request):
        queryset = self.get_queryset().filter(is_mandatory=True, is_active=True)
        serializer = PortalConsentTypeSerializer(queryset, many=True)
        return Response(serializer.data)


class PortalConsentRecordViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['account_id', 'patient_id', 'consent_type', 'consent_status', 'channel']
    ordering_fields = ['created_at', 'granted_at', 'consent_status']
    ordering = ['-created_at']

    def get_queryset(self):
        return PortalConsentRecord.objects.filter(
            tenant_id=self.request.tenant_id
        ).select_related('consent_type')

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return PortalConsentRecordWriteSerializer
        return PortalConsentRecordSerializer

    def _create_history(self, record, action, previous_status, new_status, changed_by, reason=''):
        ConsentHistory.objects.create(
            tenant_id=record.tenant_id,
            consent_record=record,
            action=action,
            previous_status=previous_status,
            new_status=new_status,
            changed_by=changed_by,
            reason=reason,
        )

    @action(detail=True, methods=['post'], url_path='grant')
    def grant(self, request, pk=None):
        record = self.get_object()
        previous_status = record.consent_status
        record.consent_status = 'granted'
        record.granted_at = timezone.now()
        record.version_consented = record.consent_type.version
        record.save(update_fields=['consent_status', 'granted_at', 'version_consented', 'updated_at'])
        self._create_history(
            record, 'granted', previous_status, 'granted',
            changed_by=request.user.id,
            reason=request.data.get('reason', ''),
        )
        serializer = PortalConsentRecordSerializer(record)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='deny')
    def deny(self, request, pk=None):
        record = self.get_object()
        previous_status = record.consent_status
        record.consent_status = 'denied'
        record.denied_at = timezone.now()
        record.save(update_fields=['consent_status', 'denied_at', 'updated_at'])
        self._create_history(
            record, 'denied', previous_status, 'denied',
            changed_by=request.user.id,
            reason=request.data.get('reason', ''),
        )
        serializer = PortalConsentRecordSerializer(record)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='withdraw')
    def withdraw(self, request, pk=None):
        record = self.get_object()
        if record.consent_status != 'granted':
            return Response(
                {'detail': 'Only granted consents can be withdrawn.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        previous_status = record.consent_status
        record.consent_status = 'withdrawn'
        record.withdrawn_at = timezone.now()
        record.save(update_fields=['consent_status', 'withdrawn_at', 'updated_at'])
        self._create_history(
            record, 'withdrawn', previous_status, 'withdrawn',
            changed_by=request.user.id,
            reason=request.data.get('reason', ''),
        )
        serializer = PortalConsentRecordSerializer(record)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='history')
    def consent_history(self, request, pk=None):
        record = self.get_object()
        history = record.history.all()
        serializer = ConsentHistorySerializer(history, many=True)
        return Response(serializer.data)


class ConsentRequestViewSet(viewsets.ModelViewSet):
    serializer_class = ConsentRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['account_id', 'patient_id', 'consent_type', 'status']
    ordering_fields = ['requested_at', 'created_at', 'expires_at']
    ordering = ['-requested_at']

    def get_queryset(self):
        return ConsentRequest.objects.filter(
            tenant_id=self.request.tenant_id
        ).select_related('consent_type')

    @action(detail=True, methods=['post'], url_path='respond')
    def respond(self, request, pk=None):
        consent_request = self.get_object()
        if consent_request.status != 'pending':
            return Response(
                {'detail': 'This consent request has already been responded to.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        response_status = request.data.get('status')
        if response_status not in ['granted', 'denied']:
            return Response(
                {'detail': 'Response status must be either "granted" or "denied".'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        consent_request.status = response_status
        consent_request.responded_at = timezone.now()
        consent_request.save(update_fields=['status', 'responded_at', 'updated_at'])
        serializer = ConsentRequestSerializer(consent_request)
        return Response(serializer.data)


class ConsentHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ConsentHistorySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['consent_record', 'action']
    ordering_fields = ['changed_at', 'created_at']
    ordering = ['-changed_at']

    def get_queryset(self):
        return ConsentHistory.objects.filter(
            tenant_id=self.request.tenant_id
        ).select_related('consent_record')
