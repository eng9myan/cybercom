from rest_framework import serializers

from products.cymed.provider_portal.clinical_tasks.models import (
    ClinicalTask,
    TaskAssignment,
    TaskComment,
    TaskEscalation,
)


class ClinicalTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClinicalTask
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class TaskAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskAssignment
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class TaskCommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskComment
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class TaskEscalationSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskEscalation
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]
