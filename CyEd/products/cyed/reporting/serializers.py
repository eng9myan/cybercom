from rest_framework import serializers

from products.cyed.reporting.models import ReportCard, ReportCardDocument, ReportCardEntry


class ReportCardEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportCardEntry
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class ReportCardSerializer(serializers.ModelSerializer):
    entries = ReportCardEntrySerializer(many=True, read_only=True)
    student_name = serializers.SerializerMethodField()

    class Meta:
        model = ReportCard
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "status", "published_on", "created_at", "updated_at"]

    def get_student_name(self, obj) -> str:
        return f"{obj.student.first_name} {obj.student.last_name}".strip()


class ReportCardDocumentSerializer(serializers.ModelSerializer):
    """Metadata only — the PDF bytes are served via the download endpoint."""

    verified = serializers.SerializerMethodField()

    class Meta:
        model = ReportCardDocument
        exclude = ["pdf_bytes"]
        read_only_fields = [f.name for f in ReportCardDocument._meta.fields if f.name != "pdf_bytes"]

    def get_verified(self, obj) -> bool:
        return obj.verify()
