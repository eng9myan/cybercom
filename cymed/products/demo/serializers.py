from rest_framework import serializers

from .models import (
    DemoEnvironment,
    DemoResetRequest,
    DemoScenario,
    DemoSession,
    DemoTenant,
    ProductTour,
)


class DemoEnvironmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = DemoEnvironment
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]
        extra_kwargs = {"admin_password_hash": {"write_only": True}}


class DemoTenantSerializer(serializers.ModelSerializer):
    class Meta:
        model = DemoTenant
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class DemoScenarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = DemoScenario
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class DemoSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DemoSession
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "started_at", "created_at", "updated_at"]


class DemoResetRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = DemoResetRequest
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class ProductTourSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductTour
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "view_count", "created_at", "updated_at"]
