from rest_framework import serializers

from products.cymed.hospital.inpatient.models import (
    DailyRound,
    DischargePlanning,
    HospitalStay,
    InpatientCarePlan,
    ProgressReview,
)


def _phi_text():
    # EncryptedText (BinaryField storage) — keep it plain text through DRF.
    return serializers.CharField(required=False, allow_blank=True)


class HospitalStaySerializer(serializers.ModelSerializer):
    class Meta:
        model = HospitalStay
        fields = "__all__"


class DailyRoundSerializer(serializers.ModelSerializer):
    subjective_notes = _phi_text()
    objective_notes = _phi_text()
    assessment_notes = _phi_text()
    plan_notes = _phi_text()

    class Meta:
        model = DailyRound
        fields = [
            "id",
            "stay",
            "clinician_id",
            "round_time",
            "subjective_notes",
            "objective_notes",
            "assessment_notes",
            "plan_notes",
        ]
        read_only_fields = ["round_time"]

    def create(self, validated_data):
        tenant_id = validated_data.get("tenant_id")
        round_obj = super().create(validated_data)

        # Canonical outbox (M9 cutover — was platform.events.OutboxEvent).
        from platform.canonical import events as canonical_events

        canonical_events.emit(
            event_type="cymed.charge.created",
            aggregate_type="BillingCharge",
            aggregate_id=round_obj.stay.admission.encounter.id,
            tenant_id=tenant_id,
            payload={
                "encounter_id": str(round_obj.stay.admission.encounter.id),
                "charge_type": "physician_round",
                "amount": 100.00,
                "currency": "AED",
                "service_code": "RND-PHY-01",
            },
        )

        return round_obj


class ProgressReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProgressReview
        fields = "__all__"


class InpatientCarePlanSerializer(serializers.ModelSerializer):
    goals = _phi_text()
    interventions = _phi_text()

    class Meta:
        model = InpatientCarePlan
        fields = "__all__"


class DischargePlanningSerializer(serializers.ModelSerializer):
    barriers_to_discharge = _phi_text()

    class Meta:
        model = DischargePlanning
        fields = "__all__"
