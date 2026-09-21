from rest_framework import serializers

from products.cycom.manufacturing.models import (
    BillOfMaterial,
    BOMComponent,
    ManufacturingOrder,
    Routing,
    RoutingOperation,
    WorkCenter,
    WorkOrder,
)


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


class WorkCenterSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkCenter
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class RoutingOperationSerializer(serializers.ModelSerializer):
    work_center_name = serializers.CharField(source="work_center.name", read_only=True)

    class Meta:
        model = RoutingOperation
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "routing", "created_at", "updated_at"]


class RoutingSerializer(serializers.ModelSerializer):
    operations = RoutingOperationSerializer(many=True, required=False)

    class Meta:
        model = Routing
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]

    def create(self, validated_data):
        operations_data = validated_data.pop("operations", [])
        routing = Routing.objects.create(**validated_data)
        for op_data in operations_data:
            RoutingOperation.objects.create(
                routing=routing, tenant_id=validated_data["tenant_id"], **op_data
            )
        routing.refresh_from_db()
        return routing


class WorkOrderSerializer(serializers.ModelSerializer):
    operation_name = serializers.CharField(source="routing_operation.name", read_only=True)
    work_center_name = serializers.CharField(source="work_center.name", read_only=True)
    actual_duration_minutes = serializers.FloatField(read_only=True)

    class Meta:
        model = WorkOrder
        fields = "__all__"
        read_only_fields = [
            "id", "tenant_id", "manufacturing_order", "routing_operation", "work_center",
            "sequence", "planned_duration_minutes", "status", "started_at", "finished_at",
            "created_at", "updated_at",
        ]


class ManufacturingOrderSerializer(serializers.ModelSerializer):
    work_orders = WorkOrderSerializer(many=True, read_only=True)
    routing_name = serializers.CharField(source="routing.name", read_only=True, default="")

    class Meta:
        model = ManufacturingOrder
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "routing", "created_at", "updated_at", "status"]
