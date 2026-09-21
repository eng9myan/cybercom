from rest_framework import serializers

from products.cycom.catalog.models import Product
from products.cycom.storefront.models import Cart, CartLine


class StorefrontProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ["id", "name", "description", "image_url", "sell_price", "sku"]


class CartLineSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    unit_price = serializers.DecimalField(source="product.sell_price", max_digits=15, decimal_places=4, read_only=True)

    class Meta:
        model = CartLine
        fields = ["id", "product", "product_name", "quantity", "unit_price"]


class CartSerializer(serializers.ModelSerializer):
    lines = CartLineSerializer(many=True, read_only=True)

    class Meta:
        model = Cart
        fields = ["id", "token", "status", "customer_name", "customer_email", "order", "lines"]
        read_only_fields = ["id", "token", "status", "order"]
