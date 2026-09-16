from core.permissions import IsAuthenticatedViaClaims
from core.viewsets import TenantScopedModelViewSet
from products.cyed.fees.models import FeeSchedule, Invoice, Payment
from products.cyed.fees.serializers import (
    FeeScheduleSerializer,
    InvoiceSerializer,
    PaymentSerializer,
)
from products.cyed.governance.access import IsFinanceOrLeadership, scope_queryset_by_student


class FeeScheduleViewSet(TenantScopedModelViewSet):
    queryset = FeeSchedule.objects.select_related("academic_year").all()
    serializer_class = FeeScheduleSerializer
    permission_classes = [IsFinanceOrLeadership]


class InvoiceViewSet(TenantScopedModelViewSet):
    queryset = Invoice.objects.select_related("student", "fee_schedule").prefetch_related("payments").all()
    serializer_class = InvoiceSerializer

    def get_permissions(self):
        # Parents may view their own children's invoices; only finance/leadership
        # may create or modify them.
        if self.action in ("list", "retrieve"):
            return [IsAuthenticatedViaClaims()]
        return [IsFinanceOrLeadership()]

    def get_queryset(self):
        qs = super().get_queryset()
        qs = scope_queryset_by_student(self.request, self.request.tenant_id, qs, student_path="student_id")
        params = self.request.query_params
        student = params.get("student")
        status_filter = params.get("status")
        if student:
            qs = qs.filter(student_id=student)
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs


class PaymentViewSet(TenantScopedModelViewSet):
    queryset = Payment.objects.select_related("invoice").all()
    serializer_class = PaymentSerializer
    permission_classes = [IsFinanceOrLeadership]

    def get_queryset(self):
        qs = super().get_queryset()
        invoice = self.request.query_params.get("invoice")
        if invoice:
            qs = qs.filter(invoice_id=invoice)
        return qs

    def perform_create(self, serializer):
        payment = serializer.save(tenant_id=self.request.tenant_id)
        # Keep the parent invoice's status in sync with recorded payments.
        payment.invoice.recalc_status()
