from rest_framework import serializers

from .models import CommissionCalculation, CommissionPolicy, CommissionTier


class CommissionTierSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommissionTier
        fields = ["id", "min_amount", "max_amount", "percentage"]


class CommissionPolicySerializer(serializers.ModelSerializer):
    tiers = CommissionTierSerializer(many=True, read_only=True)

    class Meta:
        model = CommissionPolicy
        fields = [
            "id",
            "scope",
            "scope_ref_id",
            "commission_base",
            "percentage",
            "fixed_fee",
            "min_commission",
            "max_commission",
            "delivery_excluded",
            "tips_excluded",
            "taxes_included",
            "is_exempt",
            "requires_approval",
            "approved",
            "effective_from",
            "effective_until",
            "tiers",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class CommissionCalculationSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommissionCalculation
        fields = [
            "id",
            "tenant_id",
            "reference_type",
            "reference_id",
            "policy",
            "commission_base_amount",
            "commission_amount",
            "breakdown",
            "is_refund_reversal",
            "reverses",
            "created_at",
        ]
        read_only_fields = fields
