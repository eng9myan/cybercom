from rest_framework import serializers

from .models import AccreditationRecord, ImagingQualityMetric, QualityAudit, RadiationDoseRecord


class QualityAuditSerializer(serializers.ModelSerializer):
    class Meta:
        model = QualityAudit
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class ImagingQualityMetricSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImagingQualityMetric
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class RadiationDoseRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = RadiationDoseRecord
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class AccreditationRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccreditationRecord
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]
