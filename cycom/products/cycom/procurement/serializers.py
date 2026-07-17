from rest_framework import serializers

from products.cycom.procurement.models import (
    PurchaseOrder,
    PurchaseOrderLine,
    PurchaseRequest,
    PurchaseRequestLine,
)


class PurchaseRequestLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseRequestLine
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "request", "created_at", "updated_at"]


class PurchaseRequestSerializer(serializers.ModelSerializer):
    lines = PurchaseRequestLineSerializer(many=True)

    class Meta:
        model = PurchaseRequest
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "status", "created_at", "updated_at"]

    def create(self, validated_data):
        lines_data = validated_data.pop("lines")
        request_obj = PurchaseRequest.objects.create(**validated_data)
        for line_data in lines_data:
            PurchaseRequestLine.objects.create(
                request=request_obj, tenant_id=validated_data["tenant_id"], **line_data
            )
        request_obj.refresh_from_db()
        return request_obj


class PurchaseOrderLineSerializer(serializers.ModelSerializer):
    quantity_remaining = serializers.DecimalField(max_digits=12, decimal_places=4, read_only=True)

    class Meta:
        model = PurchaseOrderLine
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "order", "quantity_received", "created_at", "updated_at"]


class PurchaseOrderSerializer(serializers.ModelSerializer):
    lines = PurchaseOrderLineSerializer(many=True)

    class Meta:
        model = PurchaseOrder
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "status", "created_at", "updated_at"]

    def create(self, validated_data):
        lines_data = validated_data.pop("lines")
        order = PurchaseOrder.objects.create(**validated_data)
        for line_data in lines_data:
            PurchaseOrderLine.objects.create(
                order=order, tenant_id=validated_data["tenant_id"], **line_data
            )
        order.refresh_from_db()
        return order
