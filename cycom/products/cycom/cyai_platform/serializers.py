from rest_framework import serializers

from products.cycom.cyai_platform.models import AgentDefinition, AgentEntitlement


class AgentDefinitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentDefinition
        fields = "__all__"


class AgentEntitlementSerializer(serializers.ModelSerializer):
    agent_key = serializers.CharField(source="agent.agent_key", read_only=True)

    class Meta:
        model = AgentEntitlement
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]
