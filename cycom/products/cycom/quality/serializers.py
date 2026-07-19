from rest_framework import serializers

from products.cycom.quality.models import QualityCheckpoint


class QualityCheckpointSerializer(serializers.ModelSerializer):
    class Meta:
        model = QualityCheckpoint
        fields = "__all__"
        read_only_fields = [
            "id", "tenant_id", "created_at", "updated_at",
            "result", "checked_by", "checked_at",
        ]
