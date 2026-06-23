from rest_framework import serializers
from products.cymed.hospital.operating_room.models import SurgicalCase, SurgicalSchedule, ProcedureBooking, ProcedureConsent, ProcedureChecklist, SurgicalTeam, SurgicalEquipment
from platform.events.models import OutboxEvent
from platform.terminology.services import TerminologyService

class SurgicalCaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = SurgicalCase
        fields = ["id", "patient", "surgeon_id", "procedure_code", "scheduled_start", "scheduled_end", "status"]

    def validate_procedure_code(self, value):
        request = self.context.get("request")
        tenant_id = getattr(request, "tenant_id", "00000000-0000-0000-0000-000000000000")
        
        # Consume Terminology Service validate
        is_valid = TerminologyService.validate(
            provider="snomed",
            code=value,
            tenant_id=str(tenant_id)
        )
        if not is_valid:
            # Fallback check under icd11
            is_valid = TerminologyService.validate(
                provider="icd11",
                code=value,
                tenant_id=str(tenant_id)
            )
        
        if not is_valid:
            raise serializers.ValidationError(
                f"Surgical procedure code '{value}' is invalid under SNOMED and ICD-11."
            )
        return value

    def update(self, instance, validated_data):
        tenant_id = instance.tenant_id
        old_status = instance.status
        new_status = validated_data.get("status", old_status)

        surgical_case = super().update(instance, validated_data)

        # Trigger Surgery Completed Event
        if new_status == "completed" and old_status != "completed":
            # Outbox surgery completed
            OutboxEvent.objects.create(
                tenant_id=tenant_id,
                topic="cymed.hospital.events",
                event_type="cymed.hospital.surgery.completed",
                payload={
                    "surgical_case_id": str(surgical_case.id),
                    "patient_id": str(surgical_case.patient.id),
                    "surgeon_id": str(surgical_case.surgeon_id),
                    "procedure_code": surgical_case.procedure_code,
                    "scheduled_start": surgical_case.scheduled_start.isoformat(),
                    "scheduled_end": surgical_case.scheduled_end.isoformat(),
                    "status": "completed"
                }
            )

            # Trigger ERP Billing Charge Event
            OutboxEvent.objects.create(
                tenant_id=tenant_id,
                topic="cymed.billing.events",
                event_type="cymed.charge.created",
                payload={
                    "encounter_id": str(surgical_case.id), # Surgical Case acts as session details reference
                    "charge_type": "or_utilization",
                    "amount": 2500.00,
                    "currency": "AED",
                    "service_code": "OR-UTIL-01"
                }
            )

            # Trigger ERP Inventory Consumed Event
            OutboxEvent.objects.create(
                tenant_id=tenant_id,
                topic="cymed.inventory.events",
                event_type="cymed.inventory.consumed",
                payload={
                    "encounter_id": str(surgical_case.id),
                    "item_code": "SURG-KIT-COMP-01",
                    "quantity": 1,
                    "unit": "kit",
                    "cost": 350.00
                }
            )

        return surgical_case

class SurgicalScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = SurgicalSchedule
        fields = "__all__"

class ProcedureBookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProcedureBooking
        fields = "__all__"

class ProcedureConsentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProcedureConsent
        fields = "__all__"

class ProcedureChecklistSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProcedureChecklist
        fields = "__all__"

class SurgicalTeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = SurgicalTeam
        fields = "__all__"

class SurgicalEquipmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = SurgicalEquipment
        fields = ["id", "surgical_case", "asset_serial", "sterilized_status", "assigned_at"]
        read_only_fields = ["assigned_at"]

    def create(self, validated_data):
        tenant_id = validated_data.get("tenant_id")
        equip = super().create(validated_data)

        # Trigger Asset Assigned outbox event
        OutboxEvent.objects.create(
            tenant_id=tenant_id,
            topic="cymed.assets.events",
            event_type="cymed.asset.assigned",
            payload={
                "surgical_case_id": str(equip.surgical_case.id),
                "asset_serial": equip.asset_serial,
                "assigned_at": equip.assigned_at.isoformat()
            }
        )

        return equip
