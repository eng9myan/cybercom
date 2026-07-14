from rest_framework import serializers

from .models import ShiftSwapApproval, ShiftSwapRequest, SwapValidationLog


class ShiftSwapRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShiftSwapRequest
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "proposed_at", "created_at", "updated_at"]


class ShiftSwapApprovalSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShiftSwapApproval
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "decided_at", "created_at", "updated_at"]


class SwapValidationLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = SwapValidationLog
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "checked_at", "created_at", "updated_at"]
