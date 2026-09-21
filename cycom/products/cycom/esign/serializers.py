import json

from rest_framework import serializers

from products.cycom.esign.models import SignRequest, SignTemplate


class JSONOrStringField(serializers.JSONField):
    """Accepts a real JSON value, or a JSON-encoded string (multipart form
    fields arrive as strings — the fields_config upload from the template
    modal is FormData.append('fields_config', JSON.stringify(...)))."""

    def to_internal_value(self, data):
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except ValueError:
                pass
        return super().to_internal_value(data)


class SignTemplateSerializer(serializers.ModelSerializer):
    fields_config = JSONOrStringField(required=False)

    class Meta:
        model = SignTemplate
        fields = ["id", "tenant_id", "name", "file", "fields_config", "created_at", "updated_at"]
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class SignRequestSerializer(serializers.ModelSerializer):
    template_id = serializers.PrimaryKeyRelatedField(
        source="template", queryset=SignTemplate.objects.all()
    )

    class Meta:
        model = SignRequest
        fields = [
            "id",
            "tenant_id",
            "template_id",
            "token",
            "signers",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "tenant_id", "token", "status", "created_at", "updated_at"]


class SignTemplatePublicSerializer(serializers.ModelSerializer):
    class Meta:
        model = SignTemplate
        fields = ["id", "name", "fields_config"]


class SignRequestPublicSerializer(serializers.ModelSerializer):
    class Meta:
        model = SignRequest
        fields = ["id", "token", "status", "signers", "created_at"]
