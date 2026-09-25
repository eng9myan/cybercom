from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from core.viewsets import TenantScopedModelViewSet
from platform.tenant.permissions import IsPlatformAdmin
from products.cycom.access.approvals import require_approval_authority
from products.cycom.procurement.models import (
    PurchaseOrder,
    PurchaseOrderLine,
    PurchaseRequest,
    RequestForQuotation,
    VendorBid,
)
from products.cycom.procurement.serializers import (
    PurchaseOrderSerializer,
    PurchaseRequestSerializer,
    RequestForQuotationSerializer,
    VendorBidSerializer,
)
from products.cycom.procurement.printing import render_purchase_order
from products.cycom.procurement.services import approve_purchase_order, receive_purchase_order, reject_purchase_order


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

    @action(detail=True, methods=["post"], url_path="approve")
    def approve(self, request, pk=None):
        pr = self.get_object()
        if pr.status != "pending_approval":
            raise ValidationError(f"Request is '{pr.status}', not pending approval.")
        # HR-4: value-based approval — the caller must hold the approver role
        # for the tier this amount falls in (admins bypass).
        require_approval_authority(request, pr.tenant_id, "purchase_request", pr.total_amount)
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

    @action(detail=True, methods=["post"], url_path="approve")
    def approve(self, request, pk=None):
        order = self.get_object()
        if order.status != "draft":
            raise ValidationError(f"PO is '{order.status}', cannot approve.")
        # HR-4: value-based approval (falls back to the purchase_request chain
        # when no purchase_order-specific policy is provisioned).
        require_approval_authority(request, order.tenant_id, "purchase_order", order.total_amount)
        approve_purchase_order(order)
        return Response(PurchaseOrderSerializer(order).data)

    @action(detail=True, methods=["post"], url_path="reject")
    def reject(self, request, pk=None):
        order = self.get_object()
        if order.status != "draft":
            raise ValidationError(f"PO is '{order.status}', cannot reject.")
        require_approval_authority(request, order.tenant_id, "purchase_order", order.total_amount)
        reject_purchase_order(order)
        return Response(PurchaseOrderSerializer(order).data)

    @action(detail=True, methods=["post"], url_path="receive")
    def receive(self, request, pk=None):
        """Full or partial goods receipt. Optional body: {"receipts": {line_id: qty}}."""
        order = self.get_object()
        receipts = request.data.get("receipts") if isinstance(request.data, dict) else None
        receive_purchase_order(order, receipts=receipts)
        order.refresh_from_db()
        return Response(PurchaseOrderSerializer(order).data)

    @action(detail=True, methods=["get"], url_path="print")
    def print_view(self, request, pk=None):
        """Print-ready HTML (Ctrl+P -> PDF, no PDF library needed)."""
        return render_purchase_order(self.get_object())


class RequestForQuotationViewSet(TenantScopedModelViewSet):
    queryset = RequestForQuotation.objects.prefetch_related("bids__lines").all()
    serializer_class = RequestForQuotationSerializer

    @action(detail=True, methods=["post"], url_path="award")
    def award(self, request, pk=None):
        """Confirm one submitted bid into a real PurchaseOrder; every other
        bid on this RFQ is marked lost. This is the only way an RFQ becomes
        a PO — there is no separate "convert" step to forget."""
        rfq = self.get_object()
        if rfq.status != "open":
            raise ValidationError(f"RFQ is '{rfq.status}', cannot award.")

        bid_id = request.data.get("bid_id")
        warehouse_id = request.data.get("warehouse")
        offset_account_id = request.data.get("offset_account")
        if not (bid_id and warehouse_id and offset_account_id):
            raise ValidationError("bid_id, warehouse, and offset_account are required.")

        try:
            winning_bid = rfq.bids.get(id=bid_id)
        except VendorBid.DoesNotExist:
            raise ValidationError("bid_id does not belong to this RFQ.")
        if winning_bid.status != "submitted":
            raise ValidationError(f"Bid is '{winning_bid.status}', must be submitted to award.")

        order = PurchaseOrder.objects.create(
            tenant_id=rfq.tenant_id,
            vendor=winning_bid.vendor,
            warehouse_id=warehouse_id,
            source_request=rfq.source_request,
            status="draft",
        )
        for line in winning_bid.lines.all():
            PurchaseOrderLine.objects.create(
                tenant_id=rfq.tenant_id,
                order=order,
                product=line.product,
                quantity=line.quantity,
                unit_cost=line.unit_cost,
                offset_account_id=offset_account_id,
            )

        winning_bid.status = "won"
        winning_bid.save(update_fields=["status", "updated_at"])
        rfq.bids.exclude(id=winning_bid.id).exclude(status="lost").update(status="lost")
        rfq.status = "awarded"
        rfq.save(update_fields=["status", "updated_at"])
        rfq.source_request.status = "converted"
        rfq.source_request.save(update_fields=["status", "updated_at"])

        order.refresh_from_db()
        return Response(PurchaseOrderSerializer(order).data, status=201)


class VendorBidViewSet(TenantScopedModelViewSet):
    queryset = VendorBid.objects.select_related("vendor", "rfq").prefetch_related("lines").all()
    serializer_class = VendorBidSerializer
    filterset_fields = ["rfq", "vendor", "status"]

    @action(detail=True, methods=["post"], url_path="submit")
    def submit(self, request, pk=None):
        bid = self.get_object()
        if bid.status != "pending":
            raise ValidationError(f"Bid is '{bid.status}', cannot submit.")
        if not bid.lines.exists():
            raise ValidationError("Bid has no lines.")
        if bid.lines.filter(unit_cost__lte=0).exists():
            raise ValidationError("Every line needs a unit_cost greater than zero to submit.")
        bid.status = "submitted"
        bid.save(update_fields=["status", "updated_at"])
        return Response(VendorBidSerializer(bid).data)
