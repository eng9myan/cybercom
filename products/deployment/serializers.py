from rest_framework import serializers
from .models import (
    DeploymentRecord, EnvironmentCheck, DeploymentStep,
    TenantProvision, BackupRecord, HealthCheckSnapshot, UpgradeRecord,
)


class DeploymentRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeploymentRecord
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class EnvironmentCheckSerializer(serializers.ModelSerializer):
    class Meta:
        model = EnvironmentCheck
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "checked_at", "created_at", "updated_at"]


class DeploymentStepSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeploymentStep
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class TenantProvisionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TenantProvision
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class BackupRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = BackupRecord
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class HealthCheckSnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = HealthCheckSnapshot
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "checked_at", "created_at", "updated_at"]


class UpgradeRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = UpgradeRecord
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]
