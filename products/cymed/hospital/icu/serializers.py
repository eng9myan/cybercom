from rest_framework import serializers

from platform.events.models import OutboxEvent
from products.cymed.hospital.icu.models import (
    CriticalEvent,
    ICUAssessment,
    ICURound,
    ICUStay,
    VentilatorRecord,
)


class ICUStaySerializer(serializers.ModelSerializer):
    class Meta:
        model = ICUStay
        fields = [
            "id",
            "stay",
            "icu_admitted_at",
            "icu_released_at",
            "ventilator_status",
            "invasive_lines_count",
        ]
        read_only_fields = ["icu_admitted_at"]

    def create(self, validated_data):
        tenant_id = validated_data.get("tenant_id")
        icu_stay = super().create(validated_data)

        # Trigger Daily ICU Billing Charge
        OutboxEvent.objects.create(
            tenant_id=tenant_id,
            topic="cymed.billing.events",
            event_type="cymed.charge.created",
            payload={
                "encounter_id": str(icu_stay.stay.admission.encounter.id),
                "charge_type": "icu_room",
                "amount": 1200.00,
                "currency": "AED",
                "service_code": "ICU-RM-01",
            },
        )

        return icu_stay


class ICURoundSerializer(serializers.ModelSerializer):
    class Meta:
        model = ICURound
        fields = "__all__"


class ICUAssessmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ICUAssessment
        fields = "__all__"

    def create(self, validated_data):
        tenant_id = validated_data.get("tenant_id")
        assess = super().create(validated_data)

        # SOFA score alert triggers
        if assess.sofa_score >= 10:
            OutboxEvent.objects.create(
                tenant_id=tenant_id,
                topic="cymed.hospital.events",
                event_type="cymed.hospital.icu.alert",
                payload={
                    "icu_stay_id": str(assess.icu_stay.id),
                    "patient_id": str(assess.icu_stay.stay.admission.encounter.patient.id),
                    "alert_type": "high_sofa_score",
                    "description": f"Critical organ failure alert. SOFA Score: {assess.sofa_score}",
                },
            )

        return assess


class VentilatorRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = VentilatorRecord
        fields = ["id", "icu_stay", "logged_at", "logged_by", "mode", "fio2_pct", "peep", "rate"]
        read_only_fields = ["logged_at"]

    def create(self, validated_data):
        tenant_id = validated_data.get("tenant_id")
        vent = super().create(validated_data)

        # Alert if oxygen requirements are critical
        if vent.fio2_pct >= 60:
            OutboxEvent.objects.create(
                tenant_id=tenant_id,
                topic="cymed.hospital.events",
                event_type="cymed.hospital.icu.alert",
                payload={
                    "icu_stay_id": str(vent.icu_stay.id),
                    "patient_id": str(vent.icu_stay.stay.admission.encounter.patient.id),
                    "alert_type": "critical_ventilator_settings",
                    "description": f"Attending critical ventilator FiO2 levels: {vent.fio2_pct}%",
                },
            )

        # Trigger Ventilator Charge Event
        OutboxEvent.objects.create(
            tenant_id=tenant_id,
            topic="cymed.billing.events",
            event_type="cymed.charge.created",
            payload={
                "encounter_id": str(vent.icu_stay.stay.admission.encounter.id),
                "charge_type": "ventilator_use",
                "amount": 450.00,
                "currency": "AED",
                "service_code": "ICU-VENT-02",
            },
        )

        return vent


class CriticalEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = CriticalEvent
        fields = ["id", "icu_stay", "event_time", "event_type", "details", "actions_taken"]
        read_only_fields = ["event_time"]

    def create(self, validated_data):
        tenant_id = validated_data.get("tenant_id")
        evt = super().create(validated_data)

        # Trigger ICU Critical Alert Event
        OutboxEvent.objects.create(
            tenant_id=tenant_id,
            topic="cymed.hospital.events",
            event_type="cymed.hospital.icu.alert",
            payload={
                "icu_stay_id": str(evt.icu_stay.id),
                "patient_id": str(evt.icu_stay.stay.admission.encounter.patient.id),
                "alert_type": f"critical_event_{evt.event_type}",
                "description": f"Critical Event: {evt.details}",
            },
        )

        return evt
