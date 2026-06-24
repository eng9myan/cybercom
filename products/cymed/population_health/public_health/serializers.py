from rest_framework import serializers
from .models import (
    PopulationGroup,
    PopulationSegment,
    HealthRisk,
    HealthGoal,
    PopulationProgram,
    NationalProvider,
    ProviderCredential,
    NationalFacility,
    FacilityAccreditation,
)


class PopulationGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = PopulationGroup
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class PopulationSegmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = PopulationSegment
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class HealthRiskSerializer(serializers.ModelSerializer):
    class Meta:
        model = HealthRisk
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class HealthGoalSerializer(serializers.ModelSerializer):
    class Meta:
        model = HealthGoal
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class PopulationProgramSerializer(serializers.ModelSerializer):
    class Meta:
        model = PopulationProgram
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class NationalProviderSerializer(serializers.ModelSerializer):
    class Meta:
        model = NationalProvider
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class ProviderCredentialSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProviderCredential
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class NationalFacilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = NationalFacility
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class FacilityAccreditationSerializer(serializers.ModelSerializer):
    class Meta:
        model = FacilityAccreditation
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]