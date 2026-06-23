from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .models import (
    TelemedicineSession,
    TelemedicineDocument,
    TelemedicineChat,
    TelemedicineRating,
)
from .serializers import (
    TelemedicineSessionSerializer,
    TelemedicineSessionWriteSerializer,
    TelemedicineDocumentSerializer,
    TelemedicineChatSerializer,
    TelemedicineRatingSerializer,
)


class TelemedicineSessionViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'session_type', 'account_id', 'patient_id', 'provider_id']
    search_fields = ['provider_name', 'chief_complaint']
    ordering_fields = ['scheduled_at', 'created_at', 'status']
    ordering = ['-scheduled_at']

    def get_queryset(self):
        return TelemedicineSession.objects.filter(
            tenant_id=self.request.tenant_id
        ).select_related()

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return TelemedicineSessionWriteSerializer
        return TelemedicineSessionSerializer

    @action(detail=True, methods=['post'], url_path='join')
    def join(self, request, pk=None):
        from django.utils import timezone
        session = self.get_object()
        if session.status not in ['scheduled', 'waiting']:
            return Response(
                {'detail': 'Session is not available to join.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        session.status = 'waiting'
        session.patient_joined_at = timezone.now()
        session.save(update_fields=['status', 'patient_joined_at', 'updated_at'])
        serializer = TelemedicineSessionSerializer(session)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='end')
    def end_session(self, request, pk=None):
        from django.utils import timezone
        session = self.get_object()
        if session.status != 'in_progress':
            return Response(
                {'detail': 'Only in-progress sessions can be ended.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        session.status = 'completed'
        session.ended_at = timezone.now()
        if session.started_at:
            delta = session.ended_at - session.started_at
            session.duration_minutes = int(delta.total_seconds() / 60)
        session.save(update_fields=['status', 'ended_at', 'duration_minutes', 'updated_at'])
        serializer = TelemedicineSessionSerializer(session)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='cancel')
    def cancel(self, request, pk=None):
        session = self.get_object()
        if session.status in ['completed', 'cancelled']:
            return Response(
                {'detail': 'Cannot cancel a completed or already cancelled session.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        session.status = 'cancelled'
        session.save(update_fields=['status', 'updated_at'])
        serializer = TelemedicineSessionSerializer(session)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='chat')
    def chat(self, request, pk=None):
        session = self.get_object()
        messages = session.chat_messages.all()
        serializer = TelemedicineChatSerializer(messages, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get', 'post'], url_path='rating')
    def rating(self, request, pk=None):
        session = self.get_object()
        if request.method == 'GET':
            try:
                serializer = TelemedicineRatingSerializer(session.session_rating)
                return Response(serializer.data)
            except TelemedicineRating.DoesNotExist:
                return Response(
                    {'detail': 'No rating found for this session.'},
                    status=status.HTTP_404_NOT_FOUND,
                )
        serializer = TelemedicineRatingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(
            session=session,
            account_id=session.account_id,
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class TelemedicineDocumentViewSet(viewsets.ModelViewSet):
    serializer_class = TelemedicineDocumentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['document_type', 'uploaded_by', 'session']
    search_fields = ['file_name']
    ordering_fields = ['uploaded_at', 'created_at']
    ordering = ['-uploaded_at']

    def get_queryset(self):
        return TelemedicineDocument.objects.filter(
            tenant_id=self.request.tenant_id
        ).select_related('session')


class TelemedicineChatViewSet(viewsets.ModelViewSet):
    serializer_class = TelemedicineChatSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['session', 'sender_type', 'is_system_message']
    ordering_fields = ['sent_at']
    ordering = ['sent_at']

    def get_queryset(self):
        return TelemedicineChat.objects.filter(
            tenant_id=self.request.tenant_id
        ).select_related('session')

    @action(detail=True, methods=['post'], url_path='mark-read')
    def mark_read(self, request, pk=None):
        from django.utils import timezone
        message = self.get_object()
        if message.read_at is None:
            message.read_at = timezone.now()
            message.save(update_fields=['read_at', 'updated_at'])
        serializer = TelemedicineChatSerializer(message)
        return Response(serializer.data)


class TelemedicineRatingViewSet(viewsets.ModelViewSet):
    serializer_class = TelemedicineRatingSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['account_id', 'would_use_again']
    ordering_fields = ['created_at', 'overall_rating']
    ordering = ['-created_at']

    def get_queryset(self):
        return TelemedicineRating.objects.filter(
            tenant_id=self.request.tenant_id
        ).select_related('session')
