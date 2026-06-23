from rest_framework import serializers

from products.cymed.provider_portal.patient_lists.models import (
    PatientList,
    PatientAssignment,
    ProviderAssignment,
    PatientCensus,
)


class PatientListSerializer(serializers.ModelSerializer):
    class Meta:
        model = PatientList
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class PatientAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = PatientAssignment
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at", "added_at"]


class ProviderAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProviderAssignment
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class PatientCensusSerializer(serializers.ModelSerializer):
    class Meta:
        model = PatientCensus
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]
