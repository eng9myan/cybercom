from rest_framework import serializers
from products.cymed.commercial.usage_metering.models import UsageMeter, UsageAlert


class UsageAlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = UsageAlert
        fields = "__all__"


class UsageMeterSerializer(serializers.ModelSerializer):
    alerts = UsageAlertSerializer(many=True, read_only=True)

    class Meta:
        model = UsageMeter
        fields = "__all__"
