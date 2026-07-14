from rest_framework import serializers

from .models import MarketplaceOrder, MarketplaceOrderLine, OrderStatusHistory


class MarketplaceOrderLineSerializer(serializers.ModelSerializer):
    line_total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = MarketplaceOrderLine
        fields = [
            "id",
            "product_id",
            "product_name_snapshot",
            "quantity",
            "unit_price",
            "item_discount",
            "notes",
            "line_total",
        ]


class OrderStatusHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderStatusHistory
        fields = ["from_status", "to_status", "reason", "actor_id", "created_at"]


class MarketplaceOrderSerializer(serializers.ModelSerializer):
    lines = MarketplaceOrderLineSerializer(many=True, read_only=True)
    status_history = OrderStatusHistorySerializer(many=True, read_only=True)

    class Meta:
        model = MarketplaceOrder
        fields = [
            "id",
            "idempotency_key",
            "tenant_id",
            "store_id",
            "customer_id",
            "category_id",
            "status",
            "fulfillment_type",
            "subtotal",
            "merchant_funded_discount",
            "cybercom_funded_discount",
            "tax_amount",
            "delivery_fee",
            "tip_amount",
            "total_amount",
            "customer_notes",
            "scheduled_for",
            "commission_calculation",
            "lines",
            "status_history",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [f for f in fields if f not in ("customer_notes", "scheduled_for")]
