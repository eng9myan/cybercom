from rest_framework import serializers

from products.cycom.quality.models import (
    CheckpointCriterionResult,
    InspectionPlan,
    InspectionPlanCriterion,
    NonConformance,
    QualityCheckpoint,
)


class InspectionPlanCriterionSerializer(serializers.ModelSerializer):
    class Meta:
        model = InspectionPlanCriterion
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "plan", "created_at", "updated_at"]


class InspectionPlanSerializer(serializers.ModelSerializer):
    criteria = InspectionPlanCriterionSerializer(many=True, required=False)

    class Meta:
        model = InspectionPlan
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]

    def create(self, validated_data):
        criteria_data = validated_data.pop("criteria", [])
        plan = InspectionPlan.objects.create(**validated_data)
        for criterion_data in criteria_data:
            InspectionPlanCriterion.objects.create(
                plan=plan, tenant_id=validated_data["tenant_id"], **criterion_data
            )
        plan.refresh_from_db()
        return plan


class CheckpointCriterionResultSerializer(serializers.ModelSerializer):
    description = serializers.CharField(source="criterion.description", read_only=True)

    class Meta:
        model = CheckpointCriterionResult
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "checkpoint", "criterion", "created_at", "updated_at"]


class NonConformanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = NonConformance
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "checkpoint", "status", "closed_at", "created_at", "updated_at"]


class QualityCheckpointSerializer(serializers.ModelSerializer):
    criterion_results = CheckpointCriterionResultSerializer(many=True, read_only=True)
    non_conformances = NonConformanceSerializer(many=True, read_only=True)
    inspection_plan_name = serializers.CharField(
        source="inspection_plan.name", read_only=True, default=""
    )

    class Meta:
        model = QualityCheckpoint
        fields = "__all__"
        read_only_fields = [
            "id", "tenant_id", "created_at", "updated_at",
            "result", "checked_by", "checked_at",
        ]
