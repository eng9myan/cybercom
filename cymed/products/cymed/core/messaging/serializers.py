from rest_framework import serializers

from products.cymed.core.messaging.models import Message, MessageThread


class MessageSerializer(serializers.ModelSerializer):
    body = serializers.CharField()

    class Meta:
        model = Message
        fields = ["id", "sender_type", "sender", "body", "read_at", "created_at"]
        read_only_fields = ["id", "sender_type", "sender", "read_at", "created_at"]


class ThreadSerializer(serializers.ModelSerializer):
    unread = serializers.SerializerMethodField()

    class Meta:
        model = MessageThread
        fields = ["id", "patient", "subject", "category", "status", "assigned_to",
                  "last_message_at", "unread", "created_at"]
        read_only_fields = ["id", "status", "last_message_at", "unread", "created_at"]

    def get_unread(self, thread) -> int:
        # Unread = written by the other side and not yet opened by the viewer.
        other = self.context.get("other_side")
        if not other:
            return 0
        return thread.messages.filter(sender_type=other, read_at__isnull=True).count()


class ThreadDetailSerializer(ThreadSerializer):
    messages = MessageSerializer(many=True, read_only=True)

    class Meta(ThreadSerializer.Meta):
        fields = ThreadSerializer.Meta.fields + ["messages"]


class NewThreadSerializer(serializers.Serializer):
    patient = serializers.UUIDField(required=False)  # staff only; patients post about themselves
    subject = serializers.CharField(max_length=200)
    category = serializers.ChoiceField(choices=[c for c, _ in MessageThread.CATEGORIES], default="general")
    body = serializers.CharField()


class ReplySerializer(serializers.Serializer):
    body = serializers.CharField()
