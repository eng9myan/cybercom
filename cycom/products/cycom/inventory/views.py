from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from core.viewsets import TenantScopedModelViewSet
from platform.tenant.permissions import IsPlatformAdmin
from products.cycom.inventory.models import (
    InternalOrder,
    InternalOrderLine,
    Product,
    StockItem,
    StockMove,
    Warehouse,
)
from products.cycom.inventory.serializers import (
    InternalOrderLineCreateSerializer,
    InternalOrderSerializer,
    ProductSerializer,
    StockItemSerializer,
    StockMoveSerializer,
    WarehouseSerializer,
)
from products.cycom.inventory.services import (
    allocate_internal_order,
    apply_stock_move,
    dispatch_internal_order,
    receive_internal_order,
)
from products.cycom.access.services import (
    restrict_to_accessible_products,
    restrict_to_accessible_warehouses,
)


class WarehouseViewSet(TenantScopedModelViewSet):
    queryset = Warehouse.objects.all()
    serializer_class = WarehouseSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        return restrict_to_accessible_warehouses(qs, self.request)


class ProductViewSet(TenantScopedModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        return restrict_to_accessible_products(qs, self.request)


class StockItemViewSet(TenantScopedModelViewSet):
    """Read-mostly — balances are only ever changed via StockMove.apply()."""

    queryset = StockItem.objects.select_related("product", "warehouse").all()
    serializer_class = StockItemSerializer
    http_method_names = ["get", "head", "options"]


class StockMoveViewSet(TenantScopedModelViewSet):
    queryset = StockMove.objects.select_related("product", "warehouse", "destination_warehouse").all()
    serializer_class = StockMoveSerializer

    def perform_create(self, serializer):
        # Transfers need explicit approval before they can move stock/value;
        # everything else can be applied straight from draft.
        status = "pending_approval" if serializer.validated_data.get("move_type") == "transfer" else "draft"
        serializer.save(tenant_id=self.request.tenant_id, status=status)

    @action(detail=True, methods=["post"], url_path="approve", permission_classes=[IsPlatformAdmin])
    def approve(self, request, pk=None):
        move = self.get_object()
        if move.status != "pending_approval":
            raise ValidationError(f"Move is '{move.status}', not pending approval.")
        move.status = "approved"
        move.save(update_fields=["status"])
        return Response(StockMoveSerializer(move).data)

    @action(detail=True, methods=["post"], url_path="reject", permission_classes=[IsPlatformAdmin])
    def reject(self, request, pk=None):
        move = self.get_object()
        if move.status != "pending_approval":
            raise ValidationError(f"Move is '{move.status}', not pending approval.")
        move.status = "rejected"
        move.save(update_fields=["status"])
        return Response(StockMoveSerializer(move).data)

    @action(detail=True, methods=["post"], url_path="apply")
    def apply(self, request, pk=None):
        move = self.get_object()
        apply_stock_move(move)
        return Response(StockMoveSerializer(move).data)


class InternalOrderLineViewSet(TenantScopedModelViewSet):
    """Standalone line creation — add items to a draft order one at a time."""

    queryset = InternalOrderLine.objects.select_related("order", "product").all()
    serializer_class = InternalOrderLineCreateSerializer
    filterset_fields = ["order"]


class InternalOrderViewSet(TenantScopedModelViewSet):
    queryset = InternalOrder.objects.prefetch_related("lines").all()
    serializer_class = InternalOrderSerializer
    filterset_fields = {"status": ["exact", "in"]}

    @action(detail=True, methods=["post"], url_path="submit")
    def submit(self, request, pk=None):
        order = self.get_object()
        if order.status != "draft":
            raise ValidationError(f"Order is '{order.status}', cannot submit.")
        if not order.lines.exists():
            raise ValidationError("Order has no lines — add at least one before submitting.")
        order.status = "submitted"
        order.save(update_fields=["status"])
        return Response(InternalOrderSerializer(order).data)

    @action(detail=True, methods=["post"], url_path="allocate")
    def allocate(self, request, pk=None):
        order = self.get_object()
        allocate_internal_order(order, request.data.get("allocations", {}))
        order.refresh_from_db()
        return Response(InternalOrderSerializer(order).data)

    @action(detail=True, methods=["post"], url_path="dispatch")
    def dispatch_shipment(self, request, pk=None):
        # Named dispatch_shipment, not dispatch — "dispatch" collides with
        # DRF's own View.dispatch(), the real request-routing entry point.
        # Naming an @action method that would silently override it and break
        # EVERY request to this viewset (list/create too, not just this
        # action) — url_path stays "dispatch" for the legacy adapter's URL.
        order = self.get_object()
        dispatch_internal_order(order)
        order.refresh_from_db()
        return Response(InternalOrderSerializer(order).data)

    @action(detail=True, methods=["post"], url_path="receive")
    def receive(self, request, pk=None):
        order = self.get_object()
        receive_internal_order(order, request.data.get("receipts", {}))
        order.refresh_from_db()
        return Response(InternalOrderSerializer(order).data)
