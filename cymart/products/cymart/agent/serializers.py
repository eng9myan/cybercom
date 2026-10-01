from rest_framework import serializers


class AgentMessageRequestSerializer(serializers.Serializer):
    text = serializers.CharField(max_length=2000)


class AgentToolCallSerializer(serializers.Serializer):
    name = serializers.CharField()
    arguments = serializers.DictField()
    output = serializers.DictField()


class AgentReplySerializer(serializers.Serializer):
    reply = serializers.CharField()
    tool_calls = AgentToolCallSerializer(many=True)
