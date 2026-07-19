from rest_framework import serializers

from products.cycom.documents.models import Document


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]
