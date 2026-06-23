from rest_framework import serializers
from .models import MessageThread, PatientMessage, MessageAttachment, SecureMessageRecipient


class MessageAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = MessageAttachment
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'uploaded_at']


class PatientMessageSerializer(serializers.ModelSerializer):
    attachments = MessageAttachmentSerializer(many=True, read_only=True)

    class Meta:
        model = PatientMessage
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'sent_at']


class SecureMessageRecipientSerializer(serializers.ModelSerializer):
    class Meta:
        model = SecureMessageRecipient
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'added_at']


class MessageThreadSerializer(serializers.ModelSerializer):
    recipients = SecureMessageRecipientSerializer(many=True, read_only=True)

    class Meta:
        model = MessageThread
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'message_count', 'unread_count']


class MessageThreadDetailSerializer(MessageThreadSerializer):
    messages = PatientMessageSerializer(many=True, read_only=True)
