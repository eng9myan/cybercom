from datetime import timedelta

from django.utils import timezone
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from core.viewsets import TenantScopedModelViewSet
from products.cycom.ar_ap.serializers import InvoiceSerializer
from products.cycom.esign.models import SignRequest, SignTemplate
from products.cycom.sales.models import QuotationTemplate, SalesOrder, SalesOrderLine
from products.cycom.sales.serializers import QuotationTemplateSerializer, SalesOrderSerializer
from products.cycom.sales.services import create_invoice_from_order


class QuotationTemplateViewSet(TenantScopedModelViewSet):
    queryset = QuotationTemplate.objects.prefetch_related("lines").all()
    serializer_class = QuotationTemplateSerializer
    filterset_fields = ["is_active"]


class SalesOrderViewSet(TenantScopedModelViewSet):
    queryset = SalesOrder.objects.select_related("sign_request").prefetch_related("lines").all()
    serializer_class = SalesOrderSerializer
    filterset_fields = ["status"]

    @action(detail=True, methods=["post"], url_path="apply-template")
    def apply_template(self, request, pk=None):
        order = self.get_object()
        if order.status != "draft":
            raise ValidationError("Only draft quotations can have a template applied.")
        template_id = request.data.get("template_id")
        if not template_id:
            raise ValidationError("template_id is required.")
        try:
            template = QuotationTemplate.objects.get(pk=template_id, tenant_id=order.tenant_id)
        except QuotationTemplate.DoesNotExist:
            raise ValidationError("template_id not found.")

        order.lines.all().delete()
        for line in template.lines.all():
            SalesOrderLine.objects.create(
                order=order,
                tenant_id=order.tenant_id,
                product=line.product,
                description=line.description,
                quantity=line.quantity,
                unit_price=line.unit_price,
                discount_percent=line.discount_percent,
                tax_percent=line.tax_percent,
            )
        if template.terms:
            order.terms = template.terms
        if template.validity_days:
            order.valid_until = (order.order_date or timezone.now().date()) + timedelta(
                days=template.validity_days
            )
        order.save(update_fields=["terms", "valid_until", "updated_at"])
        order.recompute_totals()
        return Response(SalesOrderSerializer(order).data)

    @action(detail=True, methods=["post"], url_path="request-signature")
    def request_signature(self, request, pk=None):
        """Send the quote out for e-signature via the esign app — confirm()
        then refuses to turn this quotation into an order until it comes
        back signed."""
        order = self.get_object()
        if order.status != "draft":
            raise ValidationError("Only draft quotations can be sent for signature.")
        sign_template_id = request.data.get("sign_template_id")
        if not sign_template_id:
            raise ValidationError("sign_template_id is required.")
        try:
            sign_template = SignTemplate.objects.get(pk=sign_template_id, tenant_id=order.tenant_id)
        except SignTemplate.DoesNotExist:
            raise ValidationError("sign_template_id not found.")

        signer_name = request.data.get("signer_name") or order.customer_name
        signer_email = request.data.get("signer_email", "")
        sign_request = SignRequest.objects.create(
            tenant_id=order.tenant_id,
            template=sign_template,
            signers=[{"name": signer_name, "email": signer_email}],
        )
        order.sign_request = sign_request
        order.save(update_fields=["sign_request", "updated_at"])
        return Response(SalesOrderSerializer(order).data)

    @action(detail=True, methods=["post"])
    def confirm(self, request, pk=None):
        order = self.get_object()
        if order.status != "draft":
            raise ValidationError(f"Order is '{order.status}', only quotations can be confirmed.")
        if not order.lines.exists():
            raise ValidationError("Cannot confirm an order with no lines.")
        if order.sign_request_id and order.sign_request.status != "Signed":
            raise ValidationError(
                f"Quotation is out for signature (status '{order.sign_request.status}') "
                "and cannot be confirmed until it comes back signed."
            )
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
