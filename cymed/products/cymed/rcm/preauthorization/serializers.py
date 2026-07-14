from rest_framework import serializers

from .models import (
    AuthorizationAppeal,
    AuthorizationDecision,
    AuthorizationRequest,
    Preauthorization,
)


class PreauthorizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Preauthorization
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class AuthorizationRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuthorizationRequest
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at", "request_date"]


class AuthorizationDecisionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuthorizationDecision
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class AuthorizationAppealSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuthorizationAppeal
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at", "appeal_date"]


class PreauthorizationDetailSerializer(serializers.ModelSerializer):
    """
    Extended serializer that includes nested decisions and appeal counts
    for the retrieve action.
    """

    decisions = AuthorizationDecisionSerializer(many=True, read_only=True)
    appeals = AuthorizationAppealSerializer(many=True, read_only=True)
    requests = AuthorizationRequestSerializer(many=True, read_only=True)

    class Meta:
        model = Preauthorization
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]
