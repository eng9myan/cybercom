from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions, viewsets

from .models import InstallmentPlan, PatientInvoice, PaymentMethod, PaymentTransaction
from .serializers import (
    InstallmentPlanSerializer,
    PatientInvoiceSerializer,
    PaymentMethodSerializer,
    PaymentTransactionSerializer,
)


class PatientInvoiceViewSet(viewsets.ModelViewSet):
    serializer_class = PatientInvoiceSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["status", "invoice_type", "currency"]
    ordering_fields = ["created_at", "due_date", "amount_total", "service_date"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return PatientInvoice.objects.filter(
            tenant_id=self.request.tenant_id,
            account_id=self.request.account_id,
        )


class PaymentTransactionViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentTransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["status", "payment_method", "currency"]
    ordering_fields = ["created_at", "paid_at", "amount"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return PaymentTransaction.objects.filter(
            tenant_id=self.request.tenant_id,
            account_id=self.request.account_id,
        )


class PaymentMethodViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentMethodSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["method_type", "is_active", "is_default"]
    ordering_fields = ["created_at"]
    ordering = ["-is_default", "-created_at"]

    def get_queryset(self):
        return PaymentMethod.objects.filter(
            tenant_id=self.request.tenant_id,
            account_id=self.request.account_id,
        )


class InstallmentPlanViewSet(viewsets.ModelViewSet):
    serializer_class = InstallmentPlanSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["status", "frequency"]
    ordering_fields = ["created_at", "first_payment_date", "next_payment_date"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return InstallmentPlan.objects.filter(
            tenant_id=self.request.tenant_id,
            account_id=self.request.account_id,
        )
