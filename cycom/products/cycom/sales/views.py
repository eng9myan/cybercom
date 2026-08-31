from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from core.viewsets import TenantScopedModelViewSet
from products.cycom.ar_ap.serializers import InvoiceSerializer
from products.cycom.sales.models import SalesOrder
from products.cycom.sales.serializers import SalesOrderSerializer
from products.cycom.sales.services import create_invoice_from_order


class SalesOrderViewSet(TenantScopedModelViewSet):
    queryset = SalesOrder.objects.prefetch_related("lines").all()
    serializer_class = SalesOrderSerializer
    filterset_fields = ["status"]

    @action(detail=True, methods=["post"])
    def confirm(self, request, pk=None):
        order = self.get_object()
        if order.status != "draft":
            raise ValidationError(f"Order is '{order.status}', only quotations can be confirmed.")
        if not order.lines.exists():
            raise ValidationError("Cannot confirm an order with no lines.")
        order.status = "confirmed"
        order.save(update_fields=["status", "updated_at"])
        return Response(SalesOrderSerializer(order).data)

    @action(detail=True, methods=["post"], url_path="create-invoice")
    def create_invoice(self, request, pk=None):
        order = self.get_object()
        invoice = create_invoice_from_order(order)
        return Response(
            {"order": SalesOrderSerializer(order).data, "invoice": InvoiceSerializer(invoice).data},
            status=201,
        )
