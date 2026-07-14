from rest_framework import serializers

from .models import Cart, CartItem


class CartItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = [
            "id",
            "product_id",
            "product_name_snapshot",
            "quantity",
            "unit_price",
            "item_discount",
            "notes",
        ]


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)

    class Meta:
        model = Cart
        fields = [
            "id",
            "customer_id",
            "store_id",
            "tenant_id",
            "status",
            "order_id",
            "items",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields
