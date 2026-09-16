from decimal import Decimal

from django.db.models import F
from rest_framework.decorators import action
from rest_framework.response import Response

from core.viewsets import TenantScopedModelViewSet
from products.cyed.governance.access import IsStaff
from products.cyed.inventory.models import InventoryItem, StockMove
from products.cyed.inventory.serializers import InventoryItemSerializer, StockMoveSerializer


class InventoryItemViewSet(TenantScopedModelViewSet):
    queryset = InventoryItem.objects.all()
    serializer_class = InventoryItemSerializer
    permission_classes = [IsStaff]

    def get_queryset(self):
        qs = super().get_queryset()
        params = self.request.query_params
        if params.get("reorder") in ("1", "true", "True"):
            qs = qs.filter(on_hand__lte=F("reorder_level"))
        if params.get("category"):
            qs = qs.filter(category__iexact=params["category"])
        return qs

    @action(detail=False, methods=["get"], url_path="low-stock")
    def low_stock(self, request):
        """
        Items at or below their reorder level — the low-stock alert feed.
        `critical` items are fully out of stock.
        """
        items = InventoryItem.objects.filter(
            tenant_id=request.tenant_id, on_hand__lte=F("reorder_level")
        ).order_by("category", "name")
        rows = [{
            "id": str(i.id), "name": i.name, "sku": i.sku, "category": i.category,
            "on_hand": str(i.on_hand), "reorder_level": str(i.reorder_level),
            "unit": i.unit, "location": i.location,
            "shortfall": str(Decimal(i.reorder_level) - Decimal(i.on_hand)),
            "severity": "critical" if Decimal(i.on_hand) <= 0 else "low",
        } for i in items]
        return Response({
            "count": len(rows),
            "critical": sum(1 for r in rows if r["severity"] == "critical"),
            "rows": rows,
        })

    @action(detail=False, methods=["get"], url_path="by-category")
    def by_category(self, request):
        """Stock register summarised by category (IT, furniture, textbooks, …)."""
        summary: dict = {}
        for i in InventoryItem.objects.filter(tenant_id=request.tenant_id):
            key = i.category or "uncategorised"
            row = summary.setdefault(key, {"category": key, "items": 0, "units_on_hand": Decimal("0"),
                                           "low_stock": 0})
            row["items"] += 1
            row["units_on_hand"] += Decimal(i.on_hand)
            if Decimal(i.on_hand) <= Decimal(i.reorder_level):
                row["low_stock"] += 1
        return Response({"rows": [
            {**r, "units_on_hand": str(r["units_on_hand"])}
            for r in sorted(summary.values(), key=lambda x: x["category"])
        ]})


class StockMoveViewSet(TenantScopedModelViewSet):
    queryset = StockMove.objects.select_related("item").all()
    serializer_class = StockMoveSerializer
    permission_classes = [IsStaff]

    def get_queryset(self):
        qs = super().get_queryset()
        item = self.request.query_params.get("item")
        return qs.filter(item_id=item) if item else qs

    def perform_create(self, serializer):
        move = serializer.save(tenant_id=self.request.tenant_id)
        # 'in'/'adjust' add the (signed) quantity; 'out' subtracts its magnitude.
        delta = Decimal(move.quantity)
        if move.move_type == "out":
            delta = -abs(delta)
        move.item.on_hand = Decimal(move.item.on_hand) + delta
        move.item.save(update_fields=["on_hand", "updated_at"])
