from rest_framework import serializers

from .models import (
    GrossExamination,
    MicroscopicExamination,
    PathologyCase,
    PathologyDiagnosis,
    PathologySpecimen,
)


class PathologyDiagnosisSerializer(serializers.ModelSerializer):
    class Meta:
        model = PathologyDiagnosis
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class GrossExaminationSerializer(serializers.ModelSerializer):
    class Meta:
        model = GrossExamination
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class MicroscopicExaminationSerializer(serializers.ModelSerializer):
    class Meta:
        model = MicroscopicExamination
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class PathologySpecimenSerializer(serializers.ModelSerializer):
    class Meta:
        model = PathologySpecimen
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class PathologyCaseSerializer(serializers.ModelSerializer):
    specimens = PathologySpecimenSerializer(many=True, read_only=True)

    class Meta:
        model = PathologyCase
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at", "case_number"]
