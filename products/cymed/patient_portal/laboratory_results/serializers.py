from rest_framework import serializers
from .models import (
    LabResultView,
    LabResultTrend,
    CriticalResultAcknowledgement,
    LabResultShareLink,
)


class LabResultViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = LabResultView
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class LabResultTrendSerializer(serializers.ModelSerializer):
    class Meta:
        model = LabResultTrend
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'last_updated']


class CriticalResultAcknowledgementSerializer(serializers.ModelSerializer):
    class Meta:
        model = CriticalResultAcknowledgement
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'acknowledged_at']


class LabResultShareLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = LabResultShareLink
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']
