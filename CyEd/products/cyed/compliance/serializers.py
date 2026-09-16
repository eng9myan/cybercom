from rest_framework import serializers

from core.serializers import ReadOnlyModelSerializer

from products.cyed.compliance.models import NCCDRecord, StatutoryReportLog


class NCCDRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = NCCDRecord
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]

    def validate(self, attrs):
        # (tenant_id, student, collection_year) is unique; tenant is injected on
        # save, so enforce here for a clean 400 instead of a DB IntegrityError.
        request = self.context.get("request")
        tenant_id = getattr(request, "tenant_id", None)
        student = attrs.get("student") or getattr(self.instance, "student", None)
        year = attrs.get("collection_year") or getattr(self.instance, "collection_year", None)
        qs = NCCDRecord.objects.filter(tenant_id=tenant_id, student=student, collection_year=year)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError(
                "An NCCD record already exists for this student and collection year."
            )
        return attrs


class StatutoryReportLogSerializer(ReadOnlyModelSerializer):
    class Meta:
        model = StatutoryReportLog
        fields = "__all__"
