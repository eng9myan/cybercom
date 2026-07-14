from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions, viewsets

from .models import DigitalCard, HealthPass, HealthWallet, VaccinationRecord
from .serializers import (
    DigitalCardSerializer,
    HealthPassSerializer,
    HealthWalletSerializer,
    VaccinationRecordSerializer,
)


class HealthWalletViewSet(viewsets.ModelViewSet):
    serializer_class = HealthWalletSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["is_active"]
    ordering_fields = ["created_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return HealthWallet.objects.filter(
            tenant_id=self.request.tenant_id,
            account_id=self.request.account_id,
        )


class DigitalCardViewSet(viewsets.ModelViewSet):
    serializer_class = DigitalCardSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["card_type", "is_active", "barcode_type"]
    ordering_fields = ["created_at", "display_order", "valid_until"]
    ordering = ["display_order", "-created_at"]

    def get_queryset(self):
        return DigitalCard.objects.filter(
            tenant_id=self.request.tenant_id,
            wallet_account_id=self.request.account_id,
        )


class HealthPassViewSet(viewsets.ModelViewSet):
    serializer_class = HealthPassSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["pass_type", "status", "is_verified"]
    ordering_fields = ["created_at", "issue_date", "expiry_date"]
    ordering = ["-issue_date"]

    def get_queryset(self):
        return HealthPass.objects.filter(
            tenant_id=self.request.tenant_id,
            account_id=self.request.account_id,
        )


class VaccinationRecordViewSet(viewsets.ModelViewSet):
    serializer_class = VaccinationRecordSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["vaccine_code", "cvx_code", "is_verified"]
    search_fields = ["vaccine_name", "vaccine_name_ar", "manufacturer"]
    ordering_fields = ["created_at", "administered_date", "next_dose_date"]
    ordering = ["-administered_date"]

    def get_queryset(self):
        return VaccinationRecord.objects.filter(
            tenant_id=self.request.tenant_id,
            account_id=self.request.account_id,
        )
