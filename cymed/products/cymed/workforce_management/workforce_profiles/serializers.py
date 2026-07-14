from rest_framework import serializers

from .models import ClinicalCredential, CompetencyRecord, WorkforceProfile


class WorkforceProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkforceProfile
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class ClinicalCredentialSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClinicalCredential
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class CompetencyRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompetencyRecord
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]
