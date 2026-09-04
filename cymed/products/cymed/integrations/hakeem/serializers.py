from rest_framework import serializers

from .models import HakeemMessage


class HakeemMessageSerializer(serializers.ModelSerializer):
    # EncryptedText storage — expose the decrypted value as plain text, not
    # base64, and keep the companion _bidx column out of the payload.
    subject_national_id = serializers.CharField(read_only=True)

    class Meta:
        model = HakeemMessage
        fields = ["id", "direction", "transport", "op", "subject_national_id",
                  "status", "error_message", "duration_ms", "created_at"]
        read_only_fields = fields
