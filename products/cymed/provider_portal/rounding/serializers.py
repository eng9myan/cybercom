from rest_framework import serializers
from products.cymed.provider_portal.rounding.models import (
    ClinicalRound,
    RoundTeam,
    RoundChecklist,
    RoundFinding,
    RoundAction,
)


class RoundTeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoundTeam
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class RoundChecklistSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoundChecklist
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class RoundFindingSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoundFinding
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class RoundActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoundAction
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class ClinicalRoundSerializer(serializers.ModelSerializer):
    team_members = RoundTeamSerializer(many=True, read_only=True)
    checklists = RoundChecklistSerializer(many=True, read_only=True)
    findings = RoundFindingSerializer(many=True, read_only=True)
    actions = RoundActionSerializer(many=True, read_only=True)

    class Meta:
        model = ClinicalRound
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]
