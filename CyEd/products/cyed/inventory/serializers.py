from rest_framework import serializers

from products.cyed.inventory.models import InventoryItem, StockMove


class InventoryItemSerializer(serializers.ModelSerializer):
    needs_reorder = serializers.ReadOnlyField()

    class Meta:
        model = InventoryItem
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "on_hand", "created_at", "updated_at"]


class StockMoveSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockMove
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]
