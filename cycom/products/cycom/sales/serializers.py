from rest_framework import serializers

from products.cycom.sales.models import SalesOrder, SalesOrderLine


class SalesOrderLineSerializer(serializers.ModelSerializer):
    subtotal = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    tax_amount = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)

    class Meta:
        model = SalesOrderLine
        fields = [
            "id", "product", "description", "quantity", "unit_price",
            "discount_percent", "tax_percent", "subtotal", "tax_amount",
        ]
        read_only_fields = ["id", "tenant_id", "order"]


class SalesOrderSerializer(serializers.ModelSerializer):
    lines = SalesOrderLineSerializer(many=True, required=False)

    class Meta:
        model = SalesOrder
        fields = [
            "id", "number", "customer_name", "customer_type", "order_date",
            "valid_until", "terms", "currency",
            "amount_subtotal", "amount_tax", "amount_total", "status",
            "salesperson", "notes", "invoice", "lines", "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "tenant_id", "amount_subtotal", "amount_tax", "amount_total",
            "status", "invoice", "created_at", "updated_at",
        ]

    def create(self, validated_data):
        lines_data = validated_data.pop("lines", [])
        order = SalesOrder.objects.create(**validated_data)
        for line in lines_data:
            SalesOrderLine.objects.create(order=order, tenant_id=order.tenant_id, **line)
        order.recompute_totals()
        return order

    def update(self, instance, validated_data):
        lines_data = validated_data.pop("lines", None)
        for k, v in validated_data.items():
            setattr(instance, k, v)
        instance.save()
        if lines_data is not None:
            instance.lines.all().delete()
            for line in lines_data:
                SalesOrderLine.objects.create(order=instance, tenant_id=instance.tenant_id, **line)
        instance.recompute_totals()
        return instance
