from rest_framework import serializers

from .models import (
    CriticalFinding,
    RadiologyFinding,
    RadiologyImpression,
    RadiologyReport,
    ReportAmendment,
    ReportTemplate,
    StructuredReport,
)


def _phi_text():
    # EncryptedText (BinaryField storage) — keep it plain text through DRF.
    return serializers.CharField(required=False, allow_blank=True)


class ReportTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportTemplate
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class RadiologyFindingSerializer(serializers.ModelSerializer):
    description = _phi_text()
    location_detail = _phi_text()

    class Meta:
        model = RadiologyFinding
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class RadiologyImpressionSerializer(serializers.ModelSerializer):
    impression_text = _phi_text()

    class Meta:
        model = RadiologyImpression
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class CriticalFindingSerializer(serializers.ModelSerializer):
    finding_description = _phi_text()

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
    amendment_reason = _phi_text()
    previous_findings = _phi_text()
    previous_impression = _phi_text()
    new_findings = _phi_text()
    new_impression = _phi_text()

    class Meta:
        model = ReportAmendment
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at", "amendment_date"]


class RadiologyReportSerializer(serializers.ModelSerializer):
    technique = _phi_text()
    clinical_indication = _phi_text()
    comparison_studies = _phi_text()
    findings = _phi_text()
    impression = _phi_text()
    recommendations = _phi_text()
    ai_summary = _phi_text()
    structured_findings = RadiologyFindingSerializer(many=True, read_only=True)
    structured_impressions = RadiologyImpressionSerializer(many=True, read_only=True)
    critical_findings = CriticalFindingSerializer(many=True, read_only=True)
    amendments = ReportAmendmentSerializer(many=True, read_only=True)

    class Meta:
        model = RadiologyReport
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]
