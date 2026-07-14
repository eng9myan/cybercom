from rest_framework import serializers

from platform.events.models import OutboxEvent
from platform.terminology.services import TerminologyService
from products.cymed.hospital.discharge.models import (
    DischargeChecklist,
    DischargeInstruction,
    DischargeMedication,
    FollowUpAppointment,
)


class DischargeChecklistSerializer(serializers.ModelSerializer):
    class Meta:
        model = DischargeChecklist
        fields = ["id", "stay", "task_name", "status", "updated_at"]
        read_only_fields = ["updated_at"]

    def update(self, instance, validated_data):
        tenant_id = instance.tenant_id
        old_status = instance.status
        new_status = validated_data.get("status", old_status)

        checklist = super().update(instance, validated_data)

        # Trigger discharge completed and billing charges on clearance
        if (
            new_status == "completed"
            and old_status != "completed"
            and checklist.task_name == "billing_cleared"
        ):
            # Trigger ERP Billing Charge Event for discharge processing
            OutboxEvent.objects.create(
                tenant_id=tenant_id,
                topic="cymed.billing.events",
                event_type="cymed.charge.created",
                payload={
                    "encounter_id": str(checklist.stay.admission.encounter.id),
                    "charge_type": "discharge_processing",
                    "amount": 100.00,
                    "currency": "AED",
                    "service_code": "DIS-PRC-01",
                },
            )

        return checklist


class DischargeMedicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = DischargeMedication
        fields = ["id", "stay", "medication_code", "reconciliation_action", "notes"]

    def validate_medication_code(self, value):
        request = self.context.get("request")
        tenant_id = getattr(request, "tenant_id", "00000000-0000-0000-0000-000000000000")

        is_valid = TerminologyService.validate(
            provider="snomed", code=value, tenant_id=str(tenant_id)
        )
        if not is_valid:
            is_valid = TerminologyService.validate(
                provider="icd11", code=value, tenant_id=str(tenant_id)
            )
        if not is_valid:
            raise serializers.ValidationError(f"Discharge medication code '{value}' is invalid.")
        return value


class FollowUpAppointmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = FollowUpAppointment
        fields = "__all__"


class DischargeInstructionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DischargeInstruction
        fields = "__all__"
