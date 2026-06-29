from rest_framework import serializers

from products.cymed.provider_portal.results.models import (
    CriticalResultAlert,
    ProviderResultView,
    ResultAcknowledgement,
    ResultTrend,
)


class CriticalResultAlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = CriticalResultAlert
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class ResultAcknowledgementSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResultAcknowledgement
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class ProviderResultViewSerializer(serializers.ModelSerializer):
    critical_alerts = CriticalResultAlertSerializer(many=True, read_only=True)
    acknowledgements = ResultAcknowledgementSerializer(many=True, read_only=True)

    class Meta:
        model = ProviderResultView
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]


class ResultTrendSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResultTrend
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]
