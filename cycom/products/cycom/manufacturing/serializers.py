from rest_framework import serializers

from products.cycom.manufacturing.models import BillOfMaterial, BOMComponent, ManufacturingOrder


class BOMComponentSerializer(serializers.ModelSerializer):
    class Meta:
        model = BOMComponent
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class BillOfMaterialSerializer(serializers.ModelSerializer):
    components = BOMComponentSerializer(many=True, read_only=True)

    class Meta:
        model = BillOfMaterial
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class ManufacturingOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = ManufacturingOrder
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at", "status"]
