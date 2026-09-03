"""DRF serializers for CyMed MRFF ai_diagnostics models."""
from __future__ import annotations

from rest_framework import serializers

from .models import (
    BiasAudit,
    Deployment,
    DriftMetric,
    HitlReviewItem,
    HitlReviewQueue,
    InferenceOutcome,
    ModelCard,
)


class ModelCardSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModelCard
        fields = "__all__"


class DeploymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Deployment
        fields = "__all__"


class InferenceOutcomeSerializer(serializers.ModelSerializer):
    class Meta:
        model = InferenceOutcome
        fields = "__all__"


class DriftMetricSerializer(serializers.ModelSerializer):
    class Meta:
        model = DriftMetric
        fields = "__all__"


class HitlReviewQueueSerializer(serializers.ModelSerializer):
    class Meta:
        model = HitlReviewQueue
        fields = "__all__"


class HitlReviewItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = HitlReviewItem
        fields = "__all__"


class BiasAuditSerializer(serializers.ModelSerializer):
    class Meta:
        model = BiasAudit
        fields = "__all__"
