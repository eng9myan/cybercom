from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .client import ZATCAClient
from .models import ZATCAInvoice
from .serializers import ZATCAInvoiceSerializer


class ZATCAInvoiceViewSet(viewsets.ModelViewSet):
    queryset = ZATCAInvoice.objects.all()
    serializer_class = ZATCAInvoiceSerializer

    @action(detail=True, methods=["post"], url_path="report")
    def report(self, request, pk=None):
        invoice = self.get_object()
        client = ZATCAClient()
        xml = invoice.xml_payload
        if not xml:
            return Response({"detail": "XML payload required"}, status=status.HTTP_400_BAD_REQUEST)
        result = client.report_invoice(xml)
        if "error" not in result:
            invoice.status = "reported"
            invoice.zatca_invoice_uuid = result.get("uuid", "")
            invoice.response_payload = result
            invoice.save(update_fields=["status", "zatca_invoice_uuid", "response_payload"])
        return Response(result)

    @action(detail=True, methods=["post"], url_path="clear")
    def clear(self, request, pk=None):
        invoice = self.get_object()
        if invoice.invoice_type != "b2b":
            return Response({"detail": "Only B2B invoices can be cleared"}, status=status.HTTP_400_BAD_REQUEST)
        client = ZATCAClient()
        xml = invoice.xml_payload
        if not xml:
            return Response({"detail": "XML payload required"}, status=status.HTTP_400_BAD_REQUEST)
        result = client.clear_invoice(xml)
        if "error" not in result:
            invoice.status = "cleared"
            invoice.zatca_invoice_uuid = result.get("uuid", "")
            invoice.response_payload = result
            invoice.save(update_fields=["status", "zatca_invoice_uuid", "response_payload"])
        return Response(result)

    @action(detail=True, methods=["post"], url_path="generate-qr")
    def generate_qr(self, request, pk=None):
        invoice = self.get_object()
        client = ZATCAClient()
        qr_data = client.generate_qr({
            "seller_name": request.data.get("seller_name", ""),
            "vat_number": request.data.get("vat_number", ""),
            "timestamp": request.data.get("timestamp", ""),
            "total_with_vat": str(invoice.total_with_vat),
            "vat_total": str(invoice.vat_amount),
        })
        invoice.qr_code_data = qr_data
        invoice.save(update_fields=["qr_code_data"])
        return Response({"qr_code_data": qr_data})
