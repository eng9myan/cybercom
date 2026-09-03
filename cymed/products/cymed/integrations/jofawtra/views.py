from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .client import JoFawTraClient
from .models import JoFawTraInvoice
from .serializers import JoFawTraInvoiceSerializer


class JoFawTraInvoiceViewSet(viewsets.ModelViewSet):
    queryset = JoFawTraInvoice.objects.all()
    serializer_class = JoFawTraInvoiceSerializer

    @action(detail=True, methods=["post"], url_path="submit")
    def submit(self, request, pk=None):
        invoice = self.get_object()
        client = JoFawTraClient()
        result = client.submit_invoice(invoice.raw_payload)
        if "error" not in result:
            invoice.status = "submitted"
            invoice.jofawtra_invoice_id = result.get("invoiceId", "")
            invoice.response_payload = result
            invoice.save(update_fields=["status", "jofawtra_invoice_id", "response_payload"])
        return Response(result)

    @action(detail=True, methods=["get"], url_path="status")
    def check_status(self, request, pk=None):
        invoice = self.get_object()
        if not invoice.jofawtra_invoice_id:
            return Response({"detail": "Not submitted yet"}, status=status.HTTP_400_BAD_REQUEST)
        client = JoFawTraClient()
        result = client.validate_invoice(invoice.jofawtra_invoice_id)
        return Response(result)
