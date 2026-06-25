from rest_framework import serializers
from .models import FloatPoolMember, FloatDeployment, AgencyStaffRegistration, StaffingShortageAlert


class FloatPoolMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = FloatPoolMember
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class FloatDeploymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = FloatDeployment
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "deployed_at", "created_at", "updated_at"]


class AgencyStaffRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgencyStaffRegistration
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class StaffingShortageAlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = StaffingShortageAlert
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "triggered_at", "created_at", "updated_at"]
