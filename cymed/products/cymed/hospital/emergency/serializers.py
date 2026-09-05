from rest_framework import serializers

from products.cymed.hospital.emergency.models import (
    EmergencyAcuity,
    EmergencyDisposition,
    EmergencyObservation,
    EmergencyTracking,
    EmergencyTriage,
    EmergencyVisit,
)


def _phi_text():
    # EncryptedText (BinaryField storage) - keep it plain text through DRF.
    return serializers.CharField(required=False, allow_blank=True)


class EmergencyVisitSerializer(serializers.ModelSerializer):
    presenting_complaint = _phi_text()

    class Meta:
        model = EmergencyVisit
        fields = [
            "id",
            "patient",
            "arrival_time",
            "arrival_method",
            "presenting_complaint",
            "status",
        ]
        read_only_fields = ["arrival_time"]

    def create(self, validated_data):
        tenant_id = validated_data.get("tenant_id")
        visit = super().create(validated_data)

        # Canonical outbox (M9 cutover — was platform.events.OutboxEvent).
        from platform.canonical import events as canonical_events

        canonical_events.emit(
            event_type="cymed.charge.created",
            aggregate_type="BillingCharge",
            aggregate_id=visit.id,
            tenant_id=tenant_id,
            payload={
                "encounter_id": str(visit.id),
                "charge_type": "emergency_admission",
                "amount": 250.00,
                "currency": "AED",
                "service_code": "ER-ADM-01",
            },
        )

        return visit


class EmergencyTriageSerializer(serializers.ModelSerializer):
    chief_complaint = _phi_text()

    class Meta:
        model = EmergencyTriage
        fields = ["id", "visit", "esi_level", "chief_complaint", "triage_nurse_id", "logged_at"]
        read_only_fields = ["logged_at"]

    def create(self, validated_data):
        tenant_id = validated_data.get("tenant_id")
        triage = super().create(validated_data)

        visit = triage.visit
        # Update visit status based on ESI level
        if triage.esi_level == 1:
            visit.status = "resuscitation"
        elif triage.esi_level == 2:
            visit.status = "resuscitation"
        elif triage.esi_level in [3, 4]:
            visit.status = "fast_track"
        else:
            visit.status = "fast_track"
        visit.save()

        # Trigger ICU Critical Alert Outbox Event if ESI is Critical (Level 1)
        if triage.esi_level == 1:
            # Canonical outbox (M9 cutover — was platform.events.OutboxEvent).
            from platform.canonical import events as canonical_events

            canonical_events.emit(
                event_type="cymed.hospital.icu.alert",
                aggregate_type="EmergencyVisit",
                aggregate_id=visit.id,
                tenant_id=tenant_id,
                payload={
                    "visit_id": str(visit.id),
                    "patient_id": str(visit.patient.id),
                    "alert_type": "critical_esi_level_1",
                    "description": "Patient categorized as ESI Level 1 (Resuscitation Required).",
                },
            )

        return triage


class EmergencyAcuitySerializer(serializers.ModelSerializer):
    class Meta:
        model = EmergencyAcuity
        fields = "__all__"

    def create(self, validated_data):
        tenant_id = validated_data.get("tenant_id")
        acuity = super().create(validated_data)

        # Deterioration/Sepsis alert using MEWS/NEWS2 heuristics
        if acuity.news2_score >= 5:
            # Canonical outbox (M9 cutover — was platform.events.OutboxEvent).
            from platform.canonical import events as canonical_events

            canonical_events.emit(
                event_type="cymed.hospital.icu.alert",
                aggregate_type="EmergencyVisit",
                aggregate_id=acuity.visit.id,
                tenant_id=tenant_id,
                payload={
                    "visit_id": str(acuity.visit.id),
                    "patient_id": str(acuity.visit.patient.id),
                    "alert_type": "high_news2_deterioration",
                    "description": f"Critical physiological deterioration flagged. NEWS2 score: {acuity.news2_score}",
                },
            )

        return acuity


class EmergencyDispositionSerializer(serializers.ModelSerializer):
    notes = _phi_text()

    class Meta:
        model = EmergencyDisposition
        fields = "__all__"


class EmergencyObservationSerializer(serializers.ModelSerializer):
    notes = _phi_text()

    class Meta:
        model = EmergencyObservation
        fields = "__all__"


class EmergencyTrackingSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmergencyTracking
        fields = "__all__"
