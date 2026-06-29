from rest_framework import serializers

from .models import (
    ComplianceAuditLog,
    RamadanComplianceRule,
    WardRatioConfig,
    WorkforceComplianceConfig,
)


class WorkforceComplianceConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkforceComplianceConfig
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class RamadanComplianceRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = RamadanComplianceRule
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class WardRatioConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = WardRatioConfig
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class ComplianceAuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ComplianceAuditLog
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]
