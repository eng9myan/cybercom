from rest_framework import serializers

from .models import Modality, ModalityWorklist, StudyQueue, WorklistEntry


class ModalitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Modality
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class WorklistEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = WorklistEntry
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class ModalityWorklistSerializer(serializers.ModelSerializer):
    entries = WorklistEntrySerializer(many=True, read_only=True)

    class Meta:
        model = ModalityWorklist
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class StudyQueueSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudyQueue
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]
