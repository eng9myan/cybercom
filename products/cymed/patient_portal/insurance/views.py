from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import InsuranceCard, CoverageVerification, PreauthorizationRequest, ClaimStatus
from .serializers import (
    InsuranceCardSerializer,
    CoverageVerificationSerializer,
    PreauthorizationRequestSerializer,
    ClaimStatusSerializer,
)


class InsuranceCardViewSet(viewsets.ModelViewSet):
    serializer_class = InsuranceCardSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['plan_type', 'is_active', 'is_primary']
    ordering_fields = ['created_at', 'expiry_date', 'effective_date']
    ordering = ['-is_primary', '-created_at']

    def get_queryset(self):
        return InsuranceCard.objects.filter(
            tenant_id=self.request.tenant_id,
            account_id=self.request.account_id,
        )


class CoverageVerificationViewSet(viewsets.ModelViewSet):
    serializer_class = CoverageVerificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'verification_type']
    ordering_fields = ['created_at', 'verified_at', 'service_date']
    ordering = ['-created_at']

    def get_queryset(self):
        return CoverageVerification.objects.filter(
            tenant_id=self.request.tenant_id,
            account_id=self.request.account_id,
        )


class PreauthorizationRequestViewSet(viewsets.ModelViewSet):
    serializer_class = PreauthorizationRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'service_type']
    ordering_fields = ['created_at', 'submitted_at', 'service_date', 'responded_at']
    ordering = ['-submitted_at']

    def get_queryset(self):
        return PreauthorizationRequest.objects.filter(
            tenant_id=self.request.tenant_id,
            account_id=self.request.account_id,
        )


class ClaimStatusViewSet(viewsets.ModelViewSet):
    serializer_class = ClaimStatusSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'service_type']
    ordering_fields = ['created_at', 'service_date']
    ordering = ['-service_date']

    def get_queryset(self):
        return ClaimStatus.objects.filter(
            tenant_id=self.request.tenant_id,
            account_id=self.request.account_id,
        )
