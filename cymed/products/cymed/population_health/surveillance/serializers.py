from rest_framework import serializers

from .models import (
    CaseInvestigation,
    Outbreak,
    OutbreakAlert,
    PublicHealthEvent,
    SurveillanceCase,
)


class SurveillanceCaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = SurveillanceCase
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class OutbreakSerializer(serializers.ModelSerializer):
    class Meta:
        model = Outbreak
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class OutbreakAlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = OutbreakAlert
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at", "alert_date"]


class PublicHealthEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = PublicHealthEvent
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class CaseInvestigationSerializer(serializers.ModelSerializer):
    class Meta:
        model = CaseInvestigation
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]
