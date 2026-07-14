from rest_framework import serializers

from products.cymed.core.registries.models import CohortRegistry, RegistryEntry


class RegistryEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = RegistryEntry
        fields = ["id", "registry", "patient", "joined_at", "status"]


class CohortRegistrySerializer(serializers.ModelSerializer):
    class Meta:
        model = CohortRegistry
        fields = ["id", "name", "code", "description", "is_active", "created_at", "updated_at"]
        read_only_fields = ["created_at", "updated_at"]

    def create(self, validated_data):
        request = self.context.get("request")
        if request and hasattr(request, "tenant_id"):
            validated_data["tenant_id"] = request.tenant_id
        return super().create(validated_data)
