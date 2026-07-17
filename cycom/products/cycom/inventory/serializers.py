from rest_framework import serializers

from products.cycom.inventory.models import (
    InternalOrder,
    InternalOrderLine,
    Product,
    StockItem,
    StockMove,
    Warehouse,
)


class WarehouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Warehouse
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class StockItemSerializer(serializers.ModelSerializer):
    value = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)

    class Meta:
        model = StockItem
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "quantity_on_hand", "average_cost", "created_at", "updated_at"]


class StockMoveSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockMove
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "status", "journal_entry", "created_at", "updated_at"]


class InternalOrderLineSerializer(serializers.ModelSerializer):
    """Nested-creation shape — 'order' is set by the parent InternalOrder's
    create() loop, not supplied directly."""

    class Meta:
        model = InternalOrderLine
        fields = "__all__"
        read_only_fields = [
            "id", "tenant_id", "order", "allocated_qty", "shipped_qty",
            "received_qty", "discrepancy_reason", "created_at", "updated_at",
        ]


class InternalOrderLineCreateSerializer(serializers.ModelSerializer):
    """Standalone-creation shape — lines can be added one at a time to an
    existing draft order (the real-world flow: create the order header
    first, then add items, matching how the legacy replenishment wizard
    actually calls this API)."""

    product_name = serializers.CharField(source="product.name", read_only=True)
    product_sku = serializers.CharField(source="product.sku", read_only=True)

    class Meta:
        model = InternalOrderLine
        fields = "__all__"
        read_only_fields = [
            "id", "tenant_id", "allocated_qty", "shipped_qty",
            "received_qty", "discrepancy_reason", "created_at", "updated_at",
        ]


class InternalOrderSerializer(serializers.ModelSerializer):
    # Not required at order-creation time — an order can start with zero
    # lines and have them added afterward via InternalOrderLineViewSet.
    # submit() (the draft -> submitted transition) is what actually
    # enforces "must have at least one line".
    lines = InternalOrderLineSerializer(many=True, required=False)

    class Meta:
        model = InternalOrder
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "status", "created_at", "updated_at"]

    def create(self, validated_data):
        lines_data = validated_data.pop("lines", [])
        order = InternalOrder.objects.create(**validated_data)
        for line_data in lines_data:
            InternalOrderLine.objects.create(
                order=order, tenant_id=validated_data["tenant_id"], **line_data
            )
        order.refresh_from_db()
        return order
