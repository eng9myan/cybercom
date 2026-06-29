from rest_framework import serializers

from products.cymed.provider_portal.clinical_messaging.models import (
    ClinicalGroup,
    ClinicalMessage,
    ClinicalMessageThread,
    MessageAttachment,
    MessageThreadParticipant,
)


class ClinicalMessageThreadSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClinicalMessageThread
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class ClinicalMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClinicalMessage
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at", "sent_at"]


class MessageAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = MessageAttachment
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class ClinicalGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClinicalGroup
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class MessageThreadParticipantSerializer(serializers.ModelSerializer):
    class Meta:
        model = MessageThreadParticipant
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at", "joined_at"]
