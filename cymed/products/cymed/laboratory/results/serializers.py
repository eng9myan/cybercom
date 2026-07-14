from rest_framework import serializers

from .models import (
    CriticalResult,
    LabResult,
    ReferenceRange,
    ResultApproval,
    ResultCorrection,
    ResultInterpretation,
    ResultValue,
)


class ResultValueSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResultValue
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class LabResultSerializer(serializers.ModelSerializer):
    values = ResultValueSerializer(many=True, read_only=True)

    class Meta:
        model = LabResult
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class ReferenceRangeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReferenceRange
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class ResultInterpretationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResultInterpretation
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class CriticalResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = CriticalResult
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class ResultCorrectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResultCorrection
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class ResultApprovalSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResultApproval
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]
