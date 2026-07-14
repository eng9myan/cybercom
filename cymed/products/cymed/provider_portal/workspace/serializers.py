from rest_framework import serializers

from products.cymed.provider_portal.workspace.models import (
    ProviderDashboard,
    ProviderPreferences,
    ProviderWorkspace,
    WorkspaceSession,
)


class ProviderWorkspaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProviderWorkspace
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class ProviderDashboardSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProviderDashboard
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class ProviderPreferencesSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProviderPreferences
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class WorkspaceSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkspaceSession
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at", "started_at"]
