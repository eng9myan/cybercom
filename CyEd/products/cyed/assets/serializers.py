from rest_framework import serializers

from products.cyed.assets.models import Asset


class AssetSerializer(serializers.ModelSerializer):
    annual_depreciation = serializers.SerializerMethodField()
    current_book_value = serializers.SerializerMethodField()

    class Meta:
        model = Asset
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]

    def get_annual_depreciation(self, obj) -> str:
        return str(obj.annual_depreciation())

    def get_current_book_value(self, obj) -> str:
        return str(obj.book_value())
