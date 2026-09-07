from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from . import services
from .models import EInvoiceDocument, Invoice, TaxProfile
from .serializers import (
    EInvoiceDocumentSerializer, InvoiceSerializer, TaxProfileSerializer,
)


class _Tenant:
    permission_classes = [IsAuthenticated]

    def _tid(self):
        return self.request.tenant_id


class TaxProfileViewSet(_Tenant, viewsets.ModelViewSet):
    serializer_class = TaxProfileSerializer

    def get_queryset(self):
        return TaxProfile.objects.filter(tenant_id=self._tid(), is_deleted=False)


class InvoiceViewSet(_Tenant, viewsets.ModelViewSet):
    serializer_class = InvoiceSerializer

    def get_queryset(self):
        qs = Invoice.objects.filter(tenant_id=self._tid(), is_deleted=False)
        for f in ("status", "invoice_type", "company"):
            v = self.request.query_params.get(f)
            if v:
                qs = qs.filter(**{f: v})
        return qs.select_related("company", "einvoice").prefetch_related("lines")

    @action(detail=True, methods=["post"])
    def issue(self, request, pk=None):
        """Freeze the invoice, generate the e-invoice XML + hash + QR."""
        inv = self.get_object()
        if inv.status == "draft":
            inv.status = "issued"
            inv.save(update_fields=["status", "updated_at", "version"])
        doc = services.generate(inv)
        return Response({
            "invoice": InvoiceSerializer(inv, context={"request": request}).data,
            "einvoice": EInvoiceDocumentSerializer(doc).data,
        })

    @action(detail=True, methods=["post"])
    def sign(self, request, pk=None):
        """Apply the XAdES-B signature (needs the seller CSID on the tax profile)."""
        from .signing import sign_document
        inv = self.get_object()
        doc = getattr(inv, "einvoice", None) or services.generate(inv)
        doc = sign_document(doc)
        return Response(EInvoiceDocumentSerializer(doc).data)

    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        inv = self.get_object()
        doc = getattr(inv, "einvoice", None) or services.generate(inv)
        doc = services.submit(doc)
        return Response(EInvoiceDocumentSerializer(doc).data)

    @action(detail=True, methods=["get"], url_path="xml")
    def xml(self, request, pk=None):
        doc = getattr(self.get_object(), "einvoice", None)
        if not doc or not doc.ubl_xml:
            return Response({"detail": "Not generated yet — call issue first."}, status=400)
        return Response(doc.ubl_xml, content_type="application/xml")

    @action(detail=True, methods=["get"], url_path="print")
    def print_view(self, request, pk=None):
        from .printing import render_invoice
        return render_invoice(self.get_object())


class EInvoiceDocumentViewSet(_Tenant, viewsets.ReadOnlyModelViewSet):
    serializer_class = EInvoiceDocumentSerializer

    def get_queryset(self):
        return EInvoiceDocument.objects.filter(tenant_id=self._tid()).select_related("invoice")
