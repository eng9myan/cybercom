from rest_framework import serializers

from products.cymed.core.careplans.models import CareGoal, CarePlan, CareTask


class CareGoalSerializer(serializers.ModelSerializer):
    class Meta:
        model = CareGoal
        fields = ["id", "description", "status", "target_date"]


class CareTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = CareTask
        fields = ["id", "title", "description", "status", "assigned_provider"]


class CarePlanSerializer(serializers.ModelSerializer):
    goals = CareGoalSerializer(many=True, required=False)
    tasks = CareTaskSerializer(many=True, required=False)

    class Meta:
        model = CarePlan
        fields = [
            "id",
            "patient",
            "status",
            "intent",
            "title",
            "description",
            "period_start",
            "period_end",
            "goals",
            "tasks",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def create(self, validated_data):
        goals_data = validated_data.pop("goals", [])
        tasks_data = validated_data.pop("tasks", [])

        request = self.context.get("request")
        if request and hasattr(request, "tenant_id"):
            validated_data["tenant_id"] = request.tenant_id

        cp = CarePlan.objects.create(**validated_data)

        for goal in goals_data:
            CareGoal.objects.create(careplan=cp, tenant_id=cp.tenant_id, **goal)
        for task in tasks_data:
            CareTask.objects.create(careplan=cp, tenant_id=cp.tenant_id, **task)

        # Publish outbox event
        from platform.events.models import OutboxEvent

        OutboxEvent.objects.create(
            tenant_id=cp.tenant_id,
            topic="cymed.careplan.events",
            event_type="cymed.careplan.created",
            payload={
                "careplan_id": str(cp.id),
                "patient_id": str(cp.patient.id),
                "title": cp.title,
            },
        )

        return cp
