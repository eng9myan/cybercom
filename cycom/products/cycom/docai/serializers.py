from rest_framework import serializers

from products.cycom.docai.models import ParsedDocument


class ParsedDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParsedDocument
        fields = [
            "id", "document_type", "file", "original_filename", "status",
            "extracted_data", "confidence_notes", "error_message", "reviewed_data",
            "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "status", "extracted_data", "confidence_notes", "error_message",
            "reviewed_data", "created_at", "updated_at",
        ]
