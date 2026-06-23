from rest_framework import serializers
from products.cymed.provider_portal.workforce.models import (
    ProviderSchedule,
    ShiftAssignment,
    LeaveRequest,
    AttendanceRecord,
    CredentialExpiry,
)


class ShiftAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShiftAssignment
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class ProviderScheduleSerializer(serializers.ModelSerializer):
    assignments = ShiftAssignmentSerializer(many=True, read_only=True)

    class Meta:
        model = ProviderSchedule
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class LeaveRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveRequest
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class AttendanceRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttendanceRecord
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class CredentialExpirySerializer(serializers.ModelSerializer):
    class Meta:
        model = CredentialExpiry
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]
