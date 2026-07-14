from rest_framework import serializers

from platform.cyai.models import GuardrailPolicy, InferenceLog, ModelConfig, PromptTemplate


class ModelConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModelConfig
        fields = "__all__"


class PromptTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PromptTemplate
        fields = "__all__"


class GuardrailPolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = GuardrailPolicy
        fields = "__all__"


class InferenceLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = InferenceLog
        fields = "__all__"


class InferenceRequestSerializer(serializers.Serializer):
    tenant_id = serializers.UUIDField()
    prompt = serializers.CharField()
    variables = serializers.JSONField(default=dict, required=False)


class RAGRequestSerializer(serializers.Serializer):
    tenant_id = serializers.UUIDField()
    template_id = serializers.IntegerField()
    query = serializers.CharField()
    variables = serializers.JSONField(default=dict)
