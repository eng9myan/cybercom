from rest_framework import serializers

from products.cycom.plm.models import BomComponent, EngineeringChangeOrder, ProductBOM


class BomComponentSerializer(serializers.ModelSerializer):
    class Meta:
        model = BomComponent
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class ProductBOMSerializer(serializers.ModelSerializer):
    components = BomComponentSerializer(many=True, read_only=True)

    class Meta:
        model = ProductBOM
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class EngineeringChangeOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = EngineeringChangeOrder
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]
