from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import (
    PatientAccount,
    EncounterBilling,
    Invoice,
    InvoiceLine,
    BillingAdjustment,
    Refund,
)
from .serializers import (
    PatientAccountSerializer,
    EncounterBillingSerializer,
    InvoiceSerializer,
    InvoiceWriteSerializer,
    InvoiceLineSerializer,
    BillingAdjustmentSerializer,
    RefundSerializer,
)


class PatientAccountViewSet(ModelViewSet):
    """
    CRUD for patient billing accounts.
    Supports filtering by patient_id and account_status.
    """

    queryset = PatientAccount.objects.all().order_by("-created_at")
    serializer_class = PatientAccountSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["patient_id", "account_status"]
    search_fields = ["account_number", "fhir_account_id"]
    ordering_fields = ["created_at", "account_number", "account_status"]
    ordering = ["-created_at"]


class EncounterBillingViewSet(ModelViewSet):
    """
    CRUD for encounter billing records.
    Supports filtering by patient_account, encounter_type, billing_status, and encounter_date.
    """

    queryset = EncounterBilling.objects.all().order_by("-encounter_date")
    serializer_class = EncounterBillingSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["patient_account", "encounter_type", "billing_status", "encounter_date"]
    search_fields = ["icd11_primary_diagnosis"]
    ordering_fields = ["encounter_date", "created_at", "billing_status", "total_charges"]
    ordering = ["-encounter_date"]


class InvoiceViewSet(ModelViewSet):
    """
    CRUD for invoices with an `issue` action to transition draft invoices to issued.
    Supports filtering by patient_account, invoice_type, status, and due_date.
    """

    queryset = Invoice.objects.all().order_by("-invoice_date")
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["patient_account", "invoice_type", "status", "due_date"]
    search_fields = ["invoice_number", "fhir_invoice_id"]
    ordering_fields = ["invoice_date", "due_date", "amount_total", "status"]
    ordering = ["-invoice_date"]

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return InvoiceWriteSerializer
        return InvoiceSerializer

    @action(detail=True, methods=["post"], url_path="issue")
    def issue(self, request, pk=None):
        """
        Transition invoice from draft to issued.
        Sets status to 'issued' and records the invoice_date as today if not already set.
        """
        invoice = self.get_object()

        if invoice.status != "draft":
            return Response(
                {
                    "detail": (
                        f"Cannot issue an invoice with status '{invoice.status}'. "
                        "Only 'draft' invoices can be issued."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        invoice.status = "issued"
        if not invoice.invoice_date:
            invoice.invoice_date = timezone.now().date()
        invoice.save(update_fields=["status", "invoice_date", "updated_at"])

        serializer = InvoiceSerializer(invoice, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class InvoiceLineViewSet(ModelViewSet):
    """
    CRUD for invoice line items.
    Supports filtering by invoice.
    """

    queryset = InvoiceLine.objects.all().order_by("line_number")
    serializer_class = InvoiceLineSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["invoice"]
    search_fields = ["service_code", "service_description", "icd11_diagnosis_code"]
    ordering_fields = ["line_number", "service_date", "line_total"]
    ordering = ["line_number"]


class BillingAdjustmentViewSet(ModelViewSet):
    """
    CRUD for billing adjustments on invoices.
    Supports filtering by invoice and adjustment_type.
    """

    queryset = BillingAdjustment.objects.all().order_by("-adjustment_date")
    serializer_class = BillingAdjustmentSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["invoice", "adjustment_type"]
    search_fields = ["reason"]
    ordering_fields = ["adjustment_date", "adjustment_amount", "adjustment_type"]
    ordering = ["-adjustment_date"]


class RefundViewSet(ModelViewSet):
    """
    CRUD for refunds with an `approve` action to transition pending refunds to approved.
    Supports filtering by invoice and status.
    """

    queryset = Refund.objects.all().order_by("-refund_date")
    serializer_class = RefundSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["invoice", "status"]
    search_fields = ["reason"]
    ordering_fields = ["refund_date", "refund_amount", "status"]
    ordering = ["-refund_date"]

    @action(detail=True, methods=["post"], url_path="approve")
    def approve(self, request, pk=None):
        """
        Approve a pending refund.
        Transitions status from 'pending' to 'approved'.
        """
        refund = self.get_object()

        if refund.status != "pending":
            return Response(
                {
                    "detail": (
                        f"Cannot approve a refund with status '{refund.status}'. "
                        "Only 'pending' refunds can be approved."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        refund.status = "approved"
        refund.save(update_fields=["status", "updated_at"])

        serializer = self.get_serializer(refund)
        return Response(serializer.data, status=status.HTTP_200_OK)
