from rest_framework import serializers

from .models import CDSAlert, ICDCodeSuggestion, RiskScore


class CDSAlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = CDSAlert
        fields = ["id", "patient_id", "encounter_id", "kind", "severity",
                  "title", "detail", "context", "score", "acknowledged_by",
                  "acknowledged_at", "overridden", "override_reason", "created_at"]
        read_only_fields = ["id", "created_at"]


class RiskScoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = RiskScore
        fields = ["id", "patient_id", "encounter_id", "score_type",
                  "value", "band", "features", "model_version", "created_at"]
        read_only_fields = ["id", "created_at"]


class ICDCodeSuggestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ICDCodeSuggestion
        fields = ["id", "encounter_id", "source_text", "suggestions",
                  "accepted_code", "accepted_by", "accepted_at",
                  "model_version", "created_at"]
        read_only_fields = ["id", "created_at", "model_version"]
