from rest_framework import serializers

from products.cycom.reporting.models import SavedReport
from products.cycom.reporting.registry import REPORT_SOURCES


class SavedReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = SavedReport
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]

    def validate(self, attrs):
        source = attrs.get("source", getattr(self.instance, "source", None))
        dimension = attrs.get("dimension", getattr(self.instance, "dimension", None))
        measure = attrs.get("measure", getattr(self.instance, "measure", None))

        source_cfg = REPORT_SOURCES.get(source)
        if source_cfg is None:
            raise serializers.ValidationError({"source": f"Unknown source '{source}'."})
        if dimension not in source_cfg["dimensions"]:
            raise serializers.ValidationError({"dimension": f"'{dimension}' is not valid for source '{source}'."})
        if measure not in source_cfg["measures"]:
            raise serializers.ValidationError({"measure": f"'{measure}' is not valid for source '{source}'."})
        return attrs
