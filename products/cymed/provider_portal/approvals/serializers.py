from rest_framework import serializers

from .models import (
    ApprovalRequest,
    ApprovalWorkflow,
    ApprovalDecision,
    ApprovalAuditLog,
)


class ApprovalDecisionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApprovalDecision
        fields = '__all__'


class ApprovalAuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApprovalAuditLog
        fields = '__all__'


class ApprovalRequestSerializer(serializers.ModelSerializer):
    decisions = ApprovalDecisionSerializer(many=True, read_only=True)
    audit_log = ApprovalAuditLogSerializer(many=True, read_only=True)

    class Meta:
        model = ApprovalRequest
        fields = '__all__'


class ApprovalWorkflowSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApprovalWorkflow
        fields = '__all__'
