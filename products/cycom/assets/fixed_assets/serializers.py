from rest_framework import serializers

from .models import AssetCategory, Depreciation, FixedAsset


class AssetCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = AssetCategory
        fields = [
            "id",
            "tenant_id",
            "code",
            "name",
            "useful_life_years",
            "depreciation_method",
            "salvage_pct",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class DepreciationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Depreciation
        fields = [
            "id",
            "tenant_id",
            "asset",
            "period_year",
            "period_month",
            "depreciation_amount",
            "book_value_after",
            "posted",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class FixedAssetSerializer(serializers.ModelSerializer):
    depreciations = DepreciationSerializer(many=True, read_only=True)
    category_detail = AssetCategorySerializer(source="category", read_only=True)

    class Meta:
        model = FixedAsset
        fields = [
            "id",
            "tenant_id",
            "asset_number",
            "name",
            "name_ar",
            "category",
            "category_detail",
            "acquisition_date",
            "acquisition_cost",
            "current_book_value",
            "depreciation_accumulated",
            "status",
            "location",
            "assigned_to",
            "depreciations",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
