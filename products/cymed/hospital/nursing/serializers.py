from rest_framework import serializers
from products.cymed.hospital.nursing.models import NursingShift, NursingAssignment, NursingAssessment, NursingCarePlan, NursingTask, NursingHandover
from platform.events.models import OutboxEvent

class NursingShiftSerializer(serializers.ModelSerializer):
    class Meta:
        model = NursingShift
        fields = "__all__"

class NursingAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = NursingAssignment
        fields = "__all__"

    def create(self, validated_data):
        tenant_id = validated_data.get("tenant_id")
        assignment = super().create(validated_data)

        # Trigger workforce synced outbox event
        OutboxEvent.objects.create(
            tenant_id=tenant_id,
            topic="cymed.workforce.events",
            event_type="cymed.employee.synced",
            payload={
                "assignment_id": str(assignment.id),
                "employee_id": str(assignment.nurse_id),
                "role": "nurse",
                "assigned_date": assignment.assigned_date.isoformat()
            }
        )

        return assignment

class NursingAssessmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = NursingAssessment
        fields = "__all__"

class NursingCarePlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = NursingCarePlan
        fields = "__all__"

class NursingTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = NursingTask
        fields = ["id", "admission", "task_name", "scheduled_at", "completed_at", "status"]
        read_only_fields = ["completed_at"]

    def update(self, instance, validated_data):
        tenant_id = instance.tenant_id
        status_val = validated_data.get("status")
        
        # If task changes to completed, log daily charge
        if status_val == "completed" and instance.status != "completed":
            from django.utils import timezone
            validated_data["completed_at"] = timezone.now()

            # Trigger ERP Billing Charge Event
            OutboxEvent.objects.create(
                tenant_id=tenant_id,
                topic="cymed.billing.events",
                event_type="cymed.charge.created",
                payload={
                    "encounter_id": str(instance.admission.encounter.id),
                    "charge_type": "nursing_care",
                    "amount": 75.00,
                    "currency": "AED",
                    "service_code": "NUR-SER-01"
                }
            )

        return super().update(instance, validated_data)

class NursingHandoverSerializer(serializers.ModelSerializer):
    class Meta:
        model = NursingHandover
        fields = "__all__"
