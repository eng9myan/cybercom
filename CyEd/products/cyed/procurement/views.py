from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from core.viewsets import TenantScopedModelViewSet
from products.cyed.governance.access import (
    ADMIN, LEADERSHIP, IsFinanceOrLeadership, IsStaff, _email, has_any,
)
from products.cyed.procurement import services
from products.cyed.procurement.models import (
    GoodsReceipt, PurchaseOrder, PurchaseOrderLine, PurchaseRequest, PurchaseRequestLine, Supplier,
)
from products.cyed.procurement.serializers import (
    GoodsReceiptSerializer, PurchaseOrderLineSerializer, PurchaseOrderSerializer,
    PurchaseRequestLineSerializer, PurchaseRequestSerializer, SupplierSerializer,
)


class SupplierViewSet(TenantScopedModelViewSet):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    permission_classes = [IsStaff]


class PurchaseRequestViewSet(TenantScopedModelViewSet):
    """
    Purchase requests. Any staff member may raise one; only finance/leadership
    may approve. Requests at or above the high-value threshold need a second
    (leadership) approval before they can become a purchase order.
    """

    queryset = PurchaseRequest.objects.prefetch_related("lines", "approvals").all()
    serializer_class = PurchaseRequestSerializer
    permission_classes = [IsStaff]

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.query_params.get("status"):
            qs = qs.filter(status=self.request.query_params["status"])
        if self.request.query_params.get("mine") == "1":
            qs = qs.filter(requested_by__iexact=_email(self.request))
        return qs

    def perform_create(self, serializer):
        serializer.save(tenant_id=self.request.tenant_id, requested_by=_email(self.request))

    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        try:
            pr = services.submit_request(self.get_object(), actor=_email(request))
        except services.ProcurementError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(PurchaseRequestSerializer(pr).data)

    def _decide(self, request, decision):
        if not has_any(request, {"finance", "bursar", "accounts"} | ADMIN | LEADERSHIP):
            return Response({"detail": "Only finance or leadership may decide purchase requests."},
                            status=status.HTTP_403_FORBIDDEN)
        level = int(request.data.get("level", 1))
        if level == 2 and not has_any(request, ADMIN | LEADERSHIP):
            return Response({"detail": "Level-2 approval is leadership only."},
                            status=status.HTTP_403_FORBIDDEN)
        try:
            pr = services.decide_request(
                self.get_object(), level=level, decision=decision,
                approver=_email(request), comment=request.data.get("comment", ""),
            )
        except services.SelfApprovalError as e:
            # Segregation of duties is an authorisation failure, not bad input.
            return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)
        except services.ProcurementError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(PurchaseRequestSerializer(pr).data)

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        return self._decide(request, "approved")

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        return self._decide(request, "rejected")

    @action(detail=True, methods=["post"], url_path="convert")
    def convert(self, request, pk=None):
        if not has_any(request, {"finance", "bursar", "accounts"} | ADMIN | LEADERSHIP):
            return Response({"detail": "Only finance or leadership may raise purchase orders."},
                            status=status.HTTP_403_FORBIDDEN)
        supplier = None
        if request.data.get("supplier"):
            supplier = Supplier.objects.filter(
                tenant_id=request.tenant_id, id=request.data["supplier"]
            ).first()
            if supplier is None:
                return Response({"supplier": "Unknown supplier."}, status=400)
        try:
            po = services.convert_to_order(
                self.get_object(), supplier=supplier, reference=request.data.get("reference", ""),
            )
        except services.ProcurementError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(PurchaseOrderSerializer(po).data, status=status.HTTP_201_CREATED)


class PurchaseRequestLineViewSet(TenantScopedModelViewSet):
    queryset = PurchaseRequestLine.objects.select_related("request").all()
    serializer_class = PurchaseRequestLineSerializer
    permission_classes = [IsStaff]

    def get_queryset(self):
        qs = super().get_queryset()
        pr = self.request.query_params.get("request")
        return qs.filter(request_id=pr) if pr else qs


class PurchaseOrderViewSet(TenantScopedModelViewSet):
    queryset = PurchaseOrder.objects.select_related("supplier").prefetch_related("lines", "receipts").all()
    serializer_class = PurchaseOrderSerializer
    permission_classes = [IsFinanceOrLeadership]

    @action(detail=True, methods=["post"])
    def receive(self, request, pk=None):
        """
        Receive goods against this order.

        Body: {"lines": [{"purchase_order_line_id": "...", "quantity": 5}],
               "delivery_note": "DN-123"}
        Increments inventory, records quantities, and posts Dr Inventory /
        Cr Accounts Payable. Over-receipt is rejected.
        """
        po = self.get_object()
        try:
            receipt = services.receive_goods(
                po, lines=request.data.get("lines") or [], received_by=_email(request),
                delivery_note=request.data.get("delivery_note", ""),
            )
        except services.ProcurementError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        po.refresh_from_db()
        return Response({
            "purchase_order": PurchaseOrderSerializer(po).data,
            "receipt": GoodsReceiptSerializer(receipt).data,
        })


class PurchaseOrderLineViewSet(TenantScopedModelViewSet):
    queryset = PurchaseOrderLine.objects.select_related("purchase_order").all()
    serializer_class = PurchaseOrderLineSerializer
    permission_classes = [IsFinanceOrLeadership]

    def get_queryset(self):
        qs = super().get_queryset()
        po = self.request.query_params.get("purchase_order")
        return qs.filter(purchase_order_id=po) if po else qs


class GoodsReceiptViewSet(TenantScopedModelViewSet):
    queryset = GoodsReceipt.objects.select_related("purchase_order").prefetch_related("lines").all()
    serializer_class = GoodsReceiptSerializer
    permission_classes = [IsFinanceOrLeadership]
    http_method_names = ["get", "head", "options"]  # created only via PO receive

    def get_queryset(self):
        qs = super().get_queryset()
        po = self.request.query_params.get("purchase_order")
        return qs.filter(purchase_order_id=po) if po else qs
