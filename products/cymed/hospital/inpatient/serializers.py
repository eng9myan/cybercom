from rest_framework import serializers
from products.cymed.hospital.inpatient.models import HospitalStay, DailyRound, ProgressReview, InpatientCarePlan, DischargePlanning
from platform.events.models import OutboxEvent

class HospitalStaySerializer(serializers.ModelSerializer):
    class Meta:
        model = HospitalStay
        fields = "__all__"

class DailyRoundSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyRound
        fields = ["id", "stay", "clinician_id", "round_time", "subjective_notes", "objective_notes", "assessment_notes", "plan_notes"]
        read_only_fields = ["round_time"]

    def create(self, validated_data):
        tenant_id = validated_data.get("tenant_id")
        round_obj = super().create(validated_data)

        # Trigger ERP Billing Charge Event
        OutboxEvent.objects.create(
            tenant_id=tenant_id,
            topic="cymed.billing.events",
            event_type="cymed.charge.created",
            payload={
                "encounter_id": str(round_obj.stay.admission.encounter.id),
                "charge_type": "physician_round",
                "amount": 100.00,
                "currency": "AED",
                "service_code": "RND-PHY-01"
            }
        )

        return round_obj

class ProgressReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProgressReview
        fields = "__all__"

class InpatientCarePlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = InpatientCarePlan
        fields = "__all__"

class DischargePlanningSerializer(serializers.ModelSerializer):
    class Meta:
        model = DischargePlanning
        fields = "__all__"
