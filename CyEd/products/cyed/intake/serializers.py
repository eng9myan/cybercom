from rest_framework import serializers

from products.cyed.intake.models import DocumentIntake


class DocumentIntakeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentIntake
        exclude = ["file_bytes"]
        read_only_fields = ["id", "tenant_id", "content_type", "raw_text", "extracted_fields",
                            "status", "created_at", "updated_at"]
