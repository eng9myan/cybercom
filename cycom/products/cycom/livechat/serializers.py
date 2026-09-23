from rest_framework import serializers

from products.cycom.livechat.models import ChatMessage, ChatSession


class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class ChatSessionSerializer(serializers.ModelSerializer):
    """Staff moderation — full fields, includes the token so an agent can
    link a visitor back to their session if needed."""

    class Meta:
        model = ChatSession
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "token", "created_at", "updated_at"]


class PublicChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ["id", "sender", "body", "created_at"]


class PublicChatSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatSession
        fields = ["token", "status", "created_at"]


class PublicMessageCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ["body"]

    def validate_body(self, value):
        if not value.strip():
            raise serializers.ValidationError("Message body is required.")
        return value
