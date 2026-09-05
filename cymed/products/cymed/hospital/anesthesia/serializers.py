from rest_framework import serializers

from products.cymed.hospital.anesthesia.models import (
    AnesthesiaAssessment,
    AnesthesiaPlan,
    AnesthesiaRecord,
    RecoveryAssessment,
)


def _phi_text():
    # EncryptedText (BinaryField storage) - keep it plain text through DRF.
    return serializers.CharField(required=False, allow_blank=True)


class AnesthesiaAssessmentSerializer(serializers.ModelSerializer):
    notes = _phi_text()

    class Meta:
        model = AnesthesiaAssessment
        fields = "__all__"


class AnesthesiaPlanSerializer(serializers.ModelSerializer):
    plan_description = _phi_text()

    class Meta:
        model = AnesthesiaPlan
        fields = "__all__"


class AnesthesiaRecordSerializer(serializers.ModelSerializer):
    notes = _phi_text()
    agents_used = serializers.JSONField(required=False)

    class Meta:
        model = AnesthesiaRecord
        fields = [
            "id",
            "surgical_case",
            "anesthesiologist_id",
            "start_time",
            "end_time",
            "agents_used",
            "notes",
        ]

    def create(self, validated_data):
        tenant_id = validated_data.get("tenant_id")
        record = super().create(validated_data)

        # Canonical outbox (M9 cutover — was platform.events.OutboxEvent).
        from platform.canonical import events as canonical_events

        canonical_events.emit(
            event_type="cymed.charge.created",
            aggregate_type="BillingCharge",
            aggregate_id=record.surgical_case.id,
            tenant_id=tenant_id,
            payload={
                "encounter_id": str(record.surgical_case.id),
                "charge_type": "anesthesia_services",
                "amount": 750.00,
                "currency": "AED",
                "service_code": "ANS-SRV-01",
            },
        )

        return record


class RecoveryAssessmentSerializer(serializers.ModelSerializer):
    comments = _phi_text()

    class Meta:
        model = RecoveryAssessment
        fields = "__all__"

    def create(self, validated_data):
        tenant_id = validated_data.get("tenant_id")
        assessment = super().create(validated_data)

        # Canonical outbox (M9 cutover — was platform.events.OutboxEvent).
        from platform.canonical import events as canonical_events

        canonical_events.emit(
            event_type="cymed.charge.created",
            aggregate_type="BillingCharge",
            aggregate_id=assessment.surgical_case.id,
            tenant_id=tenant_id,
            payload={
                "encounter_id": str(assessment.surgical_case.id),
                "charge_type": "anesthesia_recovery",
                "amount": 300.00,
                "currency": "AED",
                "service_code": "ANS-REC-02",
            },
        )

        return assessment
