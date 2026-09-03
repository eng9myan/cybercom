from rest_framework import serializers

from .models import NphiesInteraction


class NphiesInteractionSerializer(serializers.ModelSerializer):
    class Meta:
        model = NphiesInteraction
        fields = ["id", "kind", "status", "licensee_id", "correlation_id",
                  "duration_ms", "error_message", "created_at"]
        read_only_fields = fields
