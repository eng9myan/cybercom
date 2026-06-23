from rest_framework import serializers
from products.cymed.provider_portal.orders.models import (
    ProviderOrderRequest,
    OrderModification,
    OrderStatusUpdate,
    OrderSet,
)


class OrderModificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderModification
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class OrderStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderStatusUpdate
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class ProviderOrderRequestSerializer(serializers.ModelSerializer):
    modifications = OrderModificationSerializer(many=True, read_only=True)
    status_updates = OrderStatusUpdateSerializer(many=True, read_only=True)

    class Meta:
        model = ProviderOrderRequest
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class OrderSetSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderSet
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]
