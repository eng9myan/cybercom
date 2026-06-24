from rest_framework import serializers
from .models import QualityMeasure, QualityMeasureResult, QualityImprovement, ClinicalAudit


class QualityMeasureSerializer(serializers.ModelSerializer):
    class Meta:
        model = QualityMeasure
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class QualityMeasureResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = QualityMeasureResult
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at", "calculated_at"]


class QualityImprovementSerializer(serializers.ModelSerializer):
    class Meta:
        model = QualityImprovement
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class ClinicalAuditSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClinicalAudit
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]
