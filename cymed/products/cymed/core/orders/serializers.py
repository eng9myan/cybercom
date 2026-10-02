from rest_framework import serializers

from products.cymed.core.orders.models import Order, OrderItem, OrderResult, OrderSet, OrderSetItem


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
            "fulfilling_tenant_id",
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

        # Canonical outbox (M9 cutover — was platform.events.OutboxEvent).
        from platform.canonical import events as canonical_events

        canonical_events.emit(
            event_type="cymed.order.created",
            aggregate_type="Order",
            aggregate_id=order.id,
            tenant_id=order.tenant_id,
            payload={
                "order_id": str(order.id),
                "patient_id": str(order.patient.id),
                "type": order.order_type,
            },
        )

        return order


class OrderSetItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderSetItem
        fields = ["id", "order_type", "code", "display", "quantity", "priority",
                  "instructions", "default_selected", "sort_order"]


class OrderSetSerializer(serializers.ModelSerializer):
    items = OrderSetItemSerializer(many=True, required=False)

    class Meta:
        model = OrderSet
        fields = ["id", "code", "name", "description", "specialty", "is_active",
                  "items", "created_at", "updated_at"]
        read_only_fields = ["created_at", "updated_at"]

    def create(self, validated_data):
        items = validated_data.pop("items", [])
        order_set = OrderSet.objects.create(**validated_data)
        for item in items:
            OrderSetItem.objects.create(order_set=order_set, tenant_id=order_set.tenant_id, **item)
        return order_set

    def update(self, instance, validated_data):
        items = validated_data.pop("items", None)
        instance = super().update(instance, validated_data)
        if items is not None:  # full replacement — a set is edited as a whole
            instance.items.all().delete()
            for item in items:
                OrderSetItem.objects.create(order_set=instance, tenant_id=instance.tenant_id, **item)
        return instance


class OrderSetApplySerializer(serializers.Serializer):
    patient = serializers.UUIDField()
    encounter = serializers.UUIDField(required=False, allow_null=True)
    # Subset of the set's items to order; omitted = every default_selected item.
    item_ids = serializers.ListField(child=serializers.UUIDField(), required=False)
