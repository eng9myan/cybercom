"""DRF serializers for the cross-provider referral routing sub-app."""
from __future__ import annotations

from rest_framework import serializers

from .models import NetworkReferral, RoutingLog, RoutingRule


class RoutingRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoutingRule
        fields = "__all__"


class NetworkReferralSerializer(serializers.ModelSerializer):
    class Meta:
        model = NetworkReferral
        fields = "__all__"


class RoutingLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoutingLog
        fields = "__all__"
