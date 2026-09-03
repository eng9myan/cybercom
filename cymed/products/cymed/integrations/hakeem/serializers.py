from rest_framework import serializers

from .models import HakeemMessage


class HakeemMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = HakeemMessage
        fields = ["id", "direction", "transport", "op", "subject_national_id",
                  "status", "error_message", "duration_ms", "created_at"]
        read_only_fields = fields
