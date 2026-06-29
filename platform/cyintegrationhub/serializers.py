from rest_framework import serializers

from platform.cyintegrationhub.models import (
    ConnectorConfig,
    IntegrationPartner,
    MessageAuditLog,
    TransformationMapping,
)


class IntegrationPartnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = IntegrationPartner
        fields = "__all__"


class ConnectorConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConnectorConfig
        fields = "__all__"


class TransformationMappingSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransformationMapping
        fields = "__all__"


class MessageAuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = MessageAuditLog
        fields = "__all__"


class ConnectorExecutionRequestSerializer(serializers.Serializer):
    tenant_id = serializers.UUIDField()
    connector_type = serializers.CharField(max_length=50)
    action = serializers.CharField(max_length=20, default="send")
    payload = serializers.JSONField()
