from rest_framework import serializers

from products.cymed.core.orders.models import Order, OrderItem, OrderResult


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ["id", "code", "display", "quantity"]


class OrderResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderResult
        fields = ["id", "result_text", "result_reference_id", "recorded_at", "recorded_by"]


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, required=False)
    results = OrderResultSerializer(many=True, required=False)

    class Meta:
        model = Order
        fields = [
            "id",
            "patient",
            "encounter",
            "order_type",
            "priority",
            "status",
            "ordered_by",
            "ordered_at",
            "items",
            "results",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def create(self, validated_data):
        items_data = validated_data.pop("items", [])
        results_data = validated_data.pop("results", [])

        request = self.context.get("request")
        if request and hasattr(request, "tenant_id"):
            validated_data["tenant_id"] = request.tenant_id

        order = Order.objects.create(**validated_data)

        for item in items_data:
            OrderItem.objects.create(order=order, tenant_id=order.tenant_id, **item)
        for res in results_data:
            OrderResult.objects.create(order=order, tenant_id=order.tenant_id, **res)

        # Publish event
        from platform.events.models import OutboxEvent

        OutboxEvent.objects.create(
            tenant_id=order.tenant_id,
            topic="cymed.order.events",
            event_type="cymed.order.created",
            payload={
                "order_id": str(order.id),
                "patient_id": str(order.patient.id),
                "type": order.order_type,
            },
        )

        return order
