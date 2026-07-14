from rest_framework import serializers

from .models import CallSwapRequest, OnCallAssignment, OnCallEscalation, OnCallPage, OnCallRoster


class OnCallRosterSerializer(serializers.ModelSerializer):
    class Meta:
        model = OnCallRoster
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class OnCallAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = OnCallAssignment
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class OnCallPageSerializer(serializers.ModelSerializer):
    class Meta:
        model = OnCallPage
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "triggered_at", "created_at", "updated_at"]


class OnCallEscalationSerializer(serializers.ModelSerializer):
    class Meta:
        model = OnCallEscalation
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "triggered_at", "created_at", "updated_at"]


class CallSwapRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = CallSwapRequest
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]
