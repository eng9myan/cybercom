from rest_framework import serializers

from products.cycom.cyai_reports.models import (
    ReportBuilderSession,
    ReportDefinition,
    ReportRevision,
    ReportSchedule,
    ReportShare,
)


class ReportBuilderSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportBuilderSession
        fields = "__all__"
        read_only_fields = [
            "id", "tenant_id", "status", "messages", "draft_spec", "draft_title",
            "saved_report", "created_at", "updated_at",
        ]


class ReportRevisionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportRevision
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "report", "created_at", "updated_at"]


class ReportDefinitionSerializer(serializers.ModelSerializer):
    revisions = ReportRevisionSerializer(many=True, read_only=True)

    class Meta:
        model = ReportDefinition
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "query_spec", "current_version", "created_at", "updated_at"]


class ReportShareSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportShare
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class ReportScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportSchedule
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "last_run_at", "next_run_at", "created_at", "updated_at"]


class SendMessageSerializer(serializers.Serializer):
    content = serializers.CharField()
