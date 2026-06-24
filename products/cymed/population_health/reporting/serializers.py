from rest_framework import serializers
from .models import NationalReport, ReportTemplate, GovernmentSubmission, ReportSchedule


class NationalReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = NationalReport
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class ReportTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportTemplate
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class GovernmentSubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = GovernmentSubmission
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class ReportScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportSchedule
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]
