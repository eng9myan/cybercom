from rest_framework import serializers

from .models import ReadingAssignment, ReadingQueue, SecondOpinion, TeleradiologyCase


class ReadingQueueSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReadingQueue
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class ReadingAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReadingAssignment
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at", "assigned_at"]


class SecondOpinionSerializer(serializers.ModelSerializer):
    class Meta:
        model = SecondOpinion
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at", "requested_at"]


class TeleradiologyCaseSerializer(serializers.ModelSerializer):
    assignments = ReadingAssignmentSerializer(many=True, read_only=True)

    class Meta:
        model = TeleradiologyCase
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]
