from rest_framework import serializers
from .models import Asset, AssetDepreciation


class AssetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Asset
        fields = [
            "id",
            "name",
            "code",
            "asset_type",
            "purchase_date",
            "purchase_cost",
            "salvage_value",
            "useful_life_years",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class AssetDepreciationSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssetDepreciation
        fields = [
            "id",
            "asset",
            "depreciation_date",
            "amount",
            "accumulated_depreciation",
            "book_value",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
