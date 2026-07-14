from rest_framework import serializers

from .models import (
    Charge,
    ChargeAdjustment,
    ChargeAudit,
    ChargeItem,
    ChargeRule,
)


class ChargeItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChargeItem
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class ChargeAdjustmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChargeAdjustment
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class ChargeAuditSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChargeAudit
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class ChargeSerializer(serializers.ModelSerializer):
    items = ChargeItemSerializer(many=True, read_only=True)
    adjustments = ChargeAdjustmentSerializer(many=True, read_only=True)
    audits = ChargeAuditSerializer(many=True, read_only=True)

    class Meta:
        model = Charge
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class ChargeWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Charge
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class ChargeRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChargeRule
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]
