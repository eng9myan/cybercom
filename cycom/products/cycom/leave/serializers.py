from rest_framework import serializers

from products.cycom.leave.models import LeaveRequest, LeaveType


class LeaveTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveType
        fields = ["id", "name", "code", "is_paid", "days_per_year", "is_active"]
        read_only_fields = ["id", "tenant_id"]


class LeaveRequestSerializer(serializers.ModelSerializer):
    leave_type_code = serializers.CharField(source="leave_type.code", read_only=True)
    leave_type_name = serializers.CharField(source="leave_type.name", read_only=True)

    class Meta:
        model = LeaveRequest
        fields = [
            "id", "employee", "leave_type", "leave_type_code", "leave_type_name",
            "start_date", "end_date", "days",
            "reason", "status", "approved_by", "rejection_reason",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "tenant_id", "days", "status", "approved_by",
                            "rejection_reason", "created_at", "updated_at"]
