from rest_framework import serializers

from platform.events.models import OutboxEvent
from products.cymed.hospital.capacity_management.models import (
    CapacityRule,
    CapacityThreshold,
    OverflowUnit,
    SurgePlan,
)


class CapacityRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = CapacityRule
        fields = "__all__"


class CapacityThresholdSerializer(serializers.ModelSerializer):
    class Meta:
        model = CapacityThreshold
        fields = "__all__"


class SurgePlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SurgePlan
        fields = ["id", "name", "trigger_condition", "allocated_beds_count", "is_active"]

    def update(self, instance, validated_data):
        tenant_id = instance.tenant_id
        old_active = instance.is_active
        new_active = validated_data.get("is_active", old_active)

        plan = super().update(instance, validated_data)

        # Trigger emergency procurement if surge plan is newly activated
        if new_active and not old_active:
            OutboxEvent.objects.create(
                tenant_id=tenant_id,
                topic="cymed.procurement.events",
                event_type="cymed.procurement.requested",
                payload={
                    "surge_plan_id": str(plan.id),
                    "item_code": "SURGE-BED-EXTRA",
                    "quantity": plan.allocated_beds_count,
                    "requestor": "CapacityManagement",
                },
            )

        return plan


class OverflowUnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = OverflowUnit
        fields = "__all__"
