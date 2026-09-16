from rest_framework import serializers

from products.cyed.messaging.models import Message, MessageThread, ThreadParticipant


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = "__all__"
        # Everything is stamped from the authenticated sender. Correspondence
        # with families is a record: it is written once and never amended.
        read_only_fields = [
            "id", "tenant_id", "created_at", "updated_at",
            "thread", "sender_kind", "sender_email", "sender_name", "sent_at",
        ]


class ThreadParticipantSerializer(serializers.ModelSerializer):
    unread = serializers.SerializerMethodField()

    class Meta:
        model = ThreadParticipant
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]

    def get_unread(self, obj) -> int:
        return obj.unread_count()


class MessageThreadSerializer(serializers.ModelSerializer):
    participants = ThreadParticipantSerializer(many=True, read_only=True)
    messages = MessageSerializer(many=True, read_only=True)
    message_count = serializers.SerializerMethodField()

    class Meta:
        model = MessageThread
        fields = "__all__"
        # Threads are opened through the `open` action so participation and
        # safeguarding rules cannot be bypassed by posting a bare row.
        read_only_fields = [
            "id", "tenant_id", "created_at", "updated_at",
            "opened_by_email", "is_closed", "closed_on", "closed_by_email",
            "last_message_at",
        ]

    def get_message_count(self, obj) -> int:
        return obj.messages.count()
