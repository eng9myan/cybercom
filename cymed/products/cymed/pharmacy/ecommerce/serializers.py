"""CyMed Pharmacy E-commerce serializers."""
from rest_framework import serializers

from .models import (
    Cart,
    CartItem,
    PharmacyOrder,
    PharmacyOrderItem,
    PharmacyProduct,
    RefillRequest,
)


class PharmacyProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = PharmacyProduct
        fields = "__all__"


class RefillRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = RefillRequest
        fields = "__all__"


class CartSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cart
        fields = "__all__"


class CartItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = "__all__"


class PharmacyOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = PharmacyOrder
        fields = "__all__"


class PharmacyOrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = PharmacyOrderItem
        fields = "__all__"
