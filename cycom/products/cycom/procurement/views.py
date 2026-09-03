from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from core.viewsets import TenantScopedModelViewSet
from platform.tenant.permissions import IsPlatformAdmin
from products.cycom.procurement.models import PurchaseOrder, PurchaseOrderLine, PurchaseRequest
from products.cycom.procurement.serializers import PurchaseOrderSerializer, PurchaseRequestSerializer
from products.cycom.procurement.services import receive_purchase_order


class PurchaseRequestViewSet(TenantScopedModelViewSet):
    queryset = PurchaseRequest.objects.prefetch_related("lines").all()
    serializer_class = PurchaseRequestSerializer

    @action(detail=True, methods=["post"], url_path="submit")
    def submit(self, request, pk=None):
        pr = self.get_object()
        if pr.status != "draft":
            raise ValidationError(f"Request is '{pr.status}', cannot submit.")
        pr.status = "pending_approval"
        pr.save(update_fields=["status"])
        return Response(PurchaseRequestSerializer(pr).data)

    @action(detail=True, methods=["post"], url_path="approve", permission_classes=[IsPlatformAdmin])
    def approve(self, request, pk=None):
        pr = self.get_object()
        if pr.status != "pending_approval":
            raise ValidationError(f"Request is '{pr.status}', not pending approval.")
        pr.status = "approved"
        pr.save(update_fields=["status"])
        return Response(PurchaseRequestSerializer(pr).data)

    @action(detail=True, methods=["post"], url_path="reject", permission_classes=[IsPlatformAdmin])
    def reject(self, request, pk=None):
        pr = self.get_object()
        if pr.status != "pending_approval":
            raise ValidationError(f"Request is '{pr.status}', not pending approval.")
        pr.status = "rejected"
        pr.save(update_fields=["status"])
        return Response(PurchaseRequestSerializer(pr).data)

    @action(detail=True, methods=["post"], url_path="convert-to-po")
    def convert_to_po(self, request, pk=None):
        pr = self.get_object()
        if pr.status != "approved":
            raise ValidationError(f"Request is '{pr.status}', must be approved before converting.")
        vendor_id = request.data.get("vendor")
        warehouse_id = request.data.get("warehouse")
        offset_account_id = request.data.get("offset_account")
        if not (vendor_id and warehouse_id and offset_account_id):
            raise ValidationError("vendor, warehouse, and offset_account are required.")

        order = PurchaseOrder.objects.create(
            tenant_id=pr.tenant_id,
            vendor_id=vendor_id,
            warehouse_id=warehouse_id,
            source_request=pr,
            status="draft",
        )
        for line in pr.lines.all():
            PurchaseOrderLine.objects.create(
                tenant_id=pr.tenant_id,
                order=order,
                product=line.product,
                quantity=line.quantity,
                unit_cost=line.estimated_unit_cost,
                offset_account_id=offset_account_id,
            )
        pr.status = "converted"
        pr.save(update_fields=["status"])
        order.refresh_from_db()
        return Response(PurchaseOrderSerializer(order).data, status=201)


class PurchaseOrderViewSet(TenantScopedModelViewSet):
    queryset = PurchaseOrder.objects.prefetch_related("lines").all()
    serializer_class = PurchaseOrderSerializer

    @action(detail=True, methods=["post"], url_path="approve", permission_classes=[IsPlatformAdmin])
    def approve(self, request, pk=None):
        order = self.get_object()
        if order.status != "draft":
            raise ValidationError(f"PO is '{order.status}', cannot approve.")
        order.status = "approved"
        order.save(update_fields=["status"])
        return Response(PurchaseOrderSerializer(order).data)

    @action(detail=True, methods=["post"], url_path="receive")
    def receive(self, request, pk=None):
        """Full or partial goods receipt. Optional body: {"receipts": {line_id: qty}}."""
        order = self.get_object()
        receipts = request.data.get("receipts") if isinstance(request.data, dict) else None
        receive_purchase_order(order, receipts=receipts)
        order.refresh_from_db()
        return Response(PurchaseOrderSerializer(order).data)
