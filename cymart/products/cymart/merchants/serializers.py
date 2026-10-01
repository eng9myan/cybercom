from rest_framework import serializers

from .models import Merchant, Product


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ["id", "name", "price", "unit", "category", "is_active"]


class MerchantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Merchant
        fields = ["id", "tenant_id", "name", "kind", "cuisine", "city", "lat", "lng", "is_active"]


class MerchantWithProductsSerializer(MerchantSerializer):
    products = ProductSerializer(many=True, read_only=True)

    class Meta(MerchantSerializer.Meta):
        fields = MerchantSerializer.Meta.fields + ["products"]
