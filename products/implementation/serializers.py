from rest_framework import serializers
from .models import (
    ImplementationProject, ProjectMilestone, ProjectTask,
    CutoverChecklist, HypercareLog, MethodologyTemplate,
)


class ImplementationProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImplementationProject
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class ProjectMilestoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectMilestone
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class ProjectTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectTask
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class CutoverChecklistSerializer(serializers.ModelSerializer):
    class Meta:
        model = CutoverChecklist
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class HypercareLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = HypercareLog
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class MethodologyTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = MethodologyTemplate
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]
