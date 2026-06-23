from rest_framework import serializers
from .models import ImagingResult, StructuredMeasurement, ResultCommunication


class StructuredMeasurementSerializer(serializers.ModelSerializer):
    class Meta:
        model = StructuredMeasurement
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class ResultCommunicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResultCommunication
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at", "communicated_at"]


class ImagingResultSerializer(serializers.ModelSerializer):
    measurements = StructuredMeasurementSerializer(many=True, read_only=True)
    communications = ResultCommunicationSerializer(many=True, read_only=True)

    class Meta:
        model = ImagingResult
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]
