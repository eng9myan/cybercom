from rest_framework import serializers

from .models import (
    DiseaseRegistry,
    RegistryEnrollment,
    RegistryOutcome,
    RegistryPatient,
    RegistryStatus,
)


class DiseaseRegistrySerializer(serializers.ModelSerializer):
    class Meta:
        model = DiseaseRegistry
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class RegistryPatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegistryPatient
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class RegistryEnrollmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegistryEnrollment
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class RegistryStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegistryStatus
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class RegistryOutcomeSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegistryOutcome
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]
