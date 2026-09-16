from rest_framework import serializers

from products.cyed.ai_agents.models import (
    AgentDefinition,
    AgentInteractionLog,
    GeneratedArtifact,
    IntegrityReview,
)


class AgentDefinitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentDefinition
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]

    def validate(self, attrs):
        # (tenant_id, key) is unique at the DB level, but tenant_id is injected
        # in perform_create — not in serializer input — so DRF can't build a
        # UniqueTogetherValidator for it. Validate here to return a clean 400
        # instead of a 500 IntegrityError.
        request = self.context.get("request")
        tenant_id = getattr(request, "tenant_id", None) if request else None
        key = attrs.get("key", getattr(self.instance, "key", None))
        if tenant_id and key:
            qs = AgentDefinition.objects.filter(tenant_id=tenant_id, key=key)
            if self.instance is not None:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError({"key": "An agent with this key already exists."})
        return attrs


class AgentInteractionLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentInteractionLog
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class GeneratedArtifactSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeneratedArtifact
        fields = "__all__"
        # Created by the generator services; approved/rejected via HITL actions.
        read_only_fields = [
            "id", "tenant_id", "agent", "artifact_type", "title", "subject",
            "year_level", "curriculum_codes", "content", "status", "reviewed_by",
            "review_note", "llm_generated", "generated_by", "created_at", "updated_at",
        ]


class IntegrityReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = IntegrityReview
        fields = "__all__"
        # risk_band/signals are computed server-side; decision is set via `decide`.
        read_only_fields = [
            "id", "tenant_id", "risk_band", "signals", "decision", "decided_by",
            "decision_note", "created_at", "updated_at",
        ]
