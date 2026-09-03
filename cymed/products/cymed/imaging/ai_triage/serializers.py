"""DRF serializers for CyMed Imaging AI triage models."""

from rest_framework import serializers

from .models import AiModel, InferenceRun, TriageAlert, TriageFinding, TriageQueue


class AiModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = AiModel
        fields = "__all__"


class TriageQueueSerializer(serializers.ModelSerializer):
    class Meta:
        model = TriageQueue
        fields = "__all__"


class InferenceRunSerializer(serializers.ModelSerializer):
    class Meta:
        model = InferenceRun
        fields = "__all__"


class TriageFindingSerializer(serializers.ModelSerializer):
    class Meta:
        model = TriageFinding
        fields = "__all__"


class TriageAlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = TriageAlert
        fields = "__all__"
