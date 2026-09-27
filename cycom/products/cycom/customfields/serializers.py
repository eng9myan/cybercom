from rest_framework import serializers

from products.cycom.customfields.models import CustomFieldDefinition
from products.cycom.customfields.registry import resolve_model


class CustomFieldDefinitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomFieldDefinition
        fields = [
            "id", "model_key", "field_key", "label", "field_type", "options",
            "is_required", "is_active", "sort_order", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
        # field_key is the storage key inside the target record's `attributes`
        # JSON -- changing it after values have been saved under the old key
        # would silently orphan them, so it's only settable on create.
        extra_kwargs = {"field_key": {"required": True}}

    def validate_model_key(self, value):
        if resolve_model(value) is None:
            raise serializers.ValidationError(f"'{value}' is not a model custom fields can attach to.")
        return value

    def validate(self, attrs):
        field_type = attrs.get("field_type", getattr(self.instance, "field_type", None))
        options = attrs.get("options", getattr(self.instance, "options", None))
        if field_type == "select" and not options:
            raise serializers.ValidationError({"options": "A dropdown field needs at least one option."})
        return attrs

    def update(self, instance, validated_data):
        validated_data.pop("model_key", None)
        validated_data.pop("field_key", None)
        return super().update(instance, validated_data)
