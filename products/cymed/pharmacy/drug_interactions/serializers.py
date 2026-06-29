from rest_framework import serializers

from .models import DrugInteraction, InteractionAlert, InteractionRule, InteractionSeverity


class InteractionRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = InteractionRule
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class InteractionAlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = InteractionAlert
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at", "sent_at"]


class DrugInteractionSerializer(serializers.ModelSerializer):
    alerts = InteractionAlertSerializer(many=True, read_only=True)
    rule_code = serializers.CharField(source="rule.rule_code", read_only=True)
    management_recommendation = serializers.CharField(
        source="rule.management_recommendation", read_only=True
    )
    override_allowed = serializers.BooleanField(source="rule.override_allowed", read_only=True)

    class Meta:
        model = DrugInteraction
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at", "detected_at"]


class InteractionSeveritySerializer(serializers.ModelSerializer):
    class Meta:
        model = InteractionSeverity
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class InteractionCheckSerializer(serializers.Serializer):
    """Request body for the interaction check endpoint."""

    patient_id = serializers.UUIDField()
    drug_codes = serializers.ListField(child=serializers.CharField(), min_length=1)
    prescription_id = serializers.UUIDField(required=False, allow_null=True)
    encounter_id = serializers.UUIDField(required=False, allow_null=True)
    patient_allergies = serializers.ListField(
        child=serializers.CharField(), required=False, default=list
    )
    patient_diagnoses = serializers.ListField(
        child=serializers.CharField(), required=False, default=list
    )
    patient_age_years = serializers.IntegerField(required=False, allow_null=True)
    is_pregnant = serializers.BooleanField(required=False, default=False)
    pregnancy_trimester = serializers.CharField(required=False, allow_blank=True, default="")


class InteractionOverrideSerializer(serializers.Serializer):
    """Request body for pharmacist override."""

    override_reason = serializers.CharField(min_length=10)
