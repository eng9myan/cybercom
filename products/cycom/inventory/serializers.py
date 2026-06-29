from rest_framework import serializers

from .models import StockItem, StockMovement, Warehouse


class WarehouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Warehouse
        fields = ["id", "name", "code", "location", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class StockItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockItem
        fields = [
            "id",
            "name",
            "sku",
            "warehouse",
            "quantity",
            "unit",
            "unit_cost",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "quantity", "created_at", "updated_at"]


class StockMovementSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockMovement
        fields = [
            "id",
            "stock_item",
            "movement_type",
            "quantity",
            "reference_id",
            "movement_date",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "movement_date", "created_at", "updated_at"]
