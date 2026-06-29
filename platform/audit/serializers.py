"""
Audit & Compliance DRF serializers.
"""

from rest_framework import serializers

from .models import (
    AuditArchive,
    AuditCategory,
    AuditChain,
    AuditEntry,
    AuditEvent,
    AuditExport,
    AuditLog,
    AuditRetentionPolicy,
    AuditSignature,
    ComplianceAssessment,
    ComplianceProfile,
    ComplianceReport,
    ComplianceRule,
    ComplianceViolation,
    EvidencePackage,
    EvidenceRecord,
    LegalHold,
)


class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = "__all__"
        read_only_fields = fields


class AuditCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditCategory
        fields = "__all__"


class AuditEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditEvent
        fields = "__all__"
        read_only_fields = fields


class AuditChainSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditChain
        fields = "__all__"


class AuditEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditEntry
        fields = "__all__"


class AuditRetentionPolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditRetentionPolicy
        fields = "__all__"


class AuditArchiveSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditArchive
        fields = "__all__"
        read_only_fields = ["archived_at", "verified_at", "created_at"]


class AuditSignatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditSignature
        fields = "__all__"


class AuditExportSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditExport
        fields = "__all__"
        read_only_fields = ["status", "event_count", "download_url", "created_at", "completed_at"]


class AuditExportCreateSerializer(serializers.Serializer):
    tenant_id = serializers.UUIDField(required=False, allow_null=True)
    reason = serializers.CharField()
    filter_criteria = serializers.DictField(required=False, default=dict)
    format = serializers.ChoiceField(choices=["json", "csv", "ndjson", "parquet"], default="json")
    period_start = serializers.DateTimeField(required=False, allow_null=True)
    period_end = serializers.DateTimeField(required=False, allow_null=True)


class LegalHoldSerializer(serializers.ModelSerializer):
    is_active = serializers.BooleanField(read_only=True)

    class Meta:
        model = LegalHold
        fields = "__all__"
        read_only_fields = ["released_at", "released_by", "created_at", "updated_at"]


class LegalHoldReleaseSerializer(serializers.Serializer):
    released_by = serializers.CharField()
    reason = serializers.CharField()


class ComplianceProfileSerializer(serializers.ModelSerializer):
    rule_count = serializers.SerializerMethodField()

    class Meta:
        model = ComplianceProfile
        fields = "__all__"

    def get_rule_count(self, obj) -> int:
        return obj.rules.filter(is_active=True).count()


class ComplianceRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ComplianceRule
        fields = "__all__"


class ComplianceViolationSerializer(serializers.ModelSerializer):
    rule_detail = ComplianceRuleSerializer(source="rule", read_only=True)

    class Meta:
        model = ComplianceViolation
        fields = "__all__"
        read_only_fields = ["detected_at", "created_at", "updated_at"]


class ViolationRemediateSerializer(serializers.Serializer):
    remediated_by = serializers.CharField()
    notes = serializers.CharField(required=False, default="")


class ViolationAcceptRiskSerializer(serializers.Serializer):
    accepted_by = serializers.CharField()
    reason = serializers.CharField()


class ComplianceAssessmentSerializer(serializers.ModelSerializer):
    passed = serializers.BooleanField(read_only=True)

    class Meta:
        model = ComplianceAssessment
        fields = "__all__"
        read_only_fields = ["assessed_at", "created_at"]


class ComplianceReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = ComplianceReport
        fields = "__all__"
        read_only_fields = ["generated_at", "created_at"]


class EvidenceRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = EvidenceRecord
        fields = "__all__"
        read_only_fields = ["is_locked", "locked_at", "created_at", "updated_at"]


class EvidencePackageSerializer(serializers.ModelSerializer):
    record_count = serializers.SerializerMethodField()

    class Meta:
        model = EvidencePackage
        fields = "__all__"
        read_only_fields = [
            "is_sealed",
            "sealed_at",
            "sealed_by",
            "package_hash",
            "created_at",
            "updated_at",
        ]

    def get_record_count(self, obj) -> int:
        return obj.records.count()


class EvidencePackageSealSerializer(serializers.Serializer):
    sealed_by = serializers.CharField()


class AuditSearchSerializer(serializers.Serializer):
    tenant_id = serializers.UUIDField(required=False, allow_null=True)
    category = serializers.CharField(required=False)
    action = serializers.CharField(required=False)
    actor_user_id = serializers.CharField(required=False)
    resource_type = serializers.CharField(required=False)
    resource_id = serializers.CharField(required=False)
    status = serializers.CharField(required=False)
    data_classification = serializers.CharField(required=False)
    date_from = serializers.DateTimeField(required=False)
    date_to = serializers.DateTimeField(required=False)
    is_high_risk = serializers.BooleanField(required=False, allow_null=True)
    limit = serializers.IntegerField(required=False, default=100, min_value=1, max_value=1000)
    offset = serializers.IntegerField(required=False, default=0, min_value=0)


class ChainVerifySerializer(serializers.Serializer):
    chain_key = serializers.CharField(required=False)
