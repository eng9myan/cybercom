from rest_framework import serializers
from .models import (
    ReportTemplate, RadiologyReport, RadiologyFinding, RadiologyImpression,
    CriticalFinding, StructuredReport, ReportAmendment,
)


class ReportTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportTemplate
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class RadiologyFindingSerializer(serializers.ModelSerializer):
    class Meta:
        model = RadiologyFinding
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class RadiologyImpressionSerializer(serializers.ModelSerializer):
    class Meta:
        model = RadiologyImpression
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class CriticalFindingSerializer(serializers.ModelSerializer):
    class Meta:
        model = CriticalFinding
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class StructuredReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = StructuredReport
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class ReportAmendmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportAmendment
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at", "amendment_date"]


class RadiologyReportSerializer(serializers.ModelSerializer):
    structured_findings = RadiologyFindingSerializer(many=True, read_only=True)
    structured_impressions = RadiologyImpressionSerializer(many=True, read_only=True)
    critical_findings = CriticalFindingSerializer(many=True, read_only=True)
    amendments = ReportAmendmentSerializer(many=True, read_only=True)

    class Meta:
        model = RadiologyReport
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]
