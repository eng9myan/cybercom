from rest_framework import serializers

from products.cycom.pos.models import (
    Device,
    POSOrder,
    POSOrderLine,
    POSOrderPayment,
    POSSession,
    PosReceipt,
)


class POSSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = POSSession
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "opened_at", "closed_at", "status", "created_at", "updated_at"]


class POSOrderLineSerializer(serializers.ModelSerializer):
    subtotal = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    tax_amount = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    product_name = serializers.CharField(source="product.name", read_only=True)

    class Meta:
        model = POSOrderLine
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "order", "created_at", "updated_at"]


class POSOrderPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = POSOrderPayment
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "order", "journal_entry", "paid_at", "created_at", "updated_at"]


class POSOrderSerializer(serializers.ModelSerializer):
    lines = POSOrderLineSerializer(many=True)
    payments = POSOrderPaymentSerializer(many=True, read_only=True)
    amount_paid = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)

    class Meta:
        model = POSOrder
        fields = "__all__"
        read_only_fields = [
            "id", "tenant_id", "status", "amount_subtotal", "amount_tax", "amount_total",
            "journal_entry", "created_at", "updated_at",
        ]

    def validate_lines(self, lines):
        if not lines:
            raise serializers.ValidationError("Order must have at least one line.")
        return lines

    def create(self, validated_data):
        lines_data = validated_data.pop("lines")
        order = POSOrder.objects.create(**validated_data)
        for line_data in lines_data:
            POSOrderLine.objects.create(order=order, tenant_id=validated_data["tenant_id"], **line_data)
        order.refresh_from_db()
        return order


class DeviceSerializer(serializers.ModelSerializer):
    route = serializers.CharField(read_only=True)
    device_type_display = serializers.CharField(source="get_device_type_display", read_only=True)

    class Meta:
        model = Device
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "last_seen_at", "created_at", "updated_at"]


class PosReceiptSerializer(serializers.ModelSerializer):
    class Meta:
        model = PosReceipt
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "printed_at", "emailed_at", "created_at", "updated_at"]
