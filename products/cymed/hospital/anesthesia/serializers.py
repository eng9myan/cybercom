from rest_framework import serializers
from products.cymed.hospital.anesthesia.models import AnesthesiaAssessment, AnesthesiaPlan, AnesthesiaRecord, RecoveryAssessment
from platform.events.models import OutboxEvent

class AnesthesiaAssessmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnesthesiaAssessment
        fields = "__all__"

class AnesthesiaPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnesthesiaPlan
        fields = "__all__"

class AnesthesiaRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnesthesiaRecord
        fields = ["id", "surgical_case", "anesthesiologist_id", "start_time", "end_time", "agents_used", "notes"]

    def create(self, validated_data):
        tenant_id = validated_data.get("tenant_id")
        record = super().create(validated_data)

        # Trigger Anesthesiologist Charge
        OutboxEvent.objects.create(
            tenant_id=tenant_id,
            topic="cymed.billing.events",
            event_type="cymed.charge.created",
            payload={
                "encounter_id": str(record.surgical_case.id),
                "charge_type": "anesthesia_services",
                "amount": 750.00,
                "currency": "AED",
                "service_code": "ANS-SRV-01"
            }
        )

        return record

class RecoveryAssessmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecoveryAssessment
        fields = "__all__"

    def create(self, validated_data):
        tenant_id = validated_data.get("tenant_id")
        assessment = super().create(validated_data)

        # Trigger Post-Anesthesia Recovery Charge Event
        OutboxEvent.objects.create(
            tenant_id=tenant_id,
            topic="cymed.billing.events",
            event_type="cymed.charge.created",
            payload={
                "encounter_id": str(assessment.surgical_case.id),
                "charge_type": "anesthesia_recovery",
                "amount": 300.00,
                "currency": "AED",
                "service_code": "ANS-REC-02"
            }
        )

        return assessment
