"""DRF serializers for teleradiology marketplace resources."""

from __future__ import annotations

from rest_framework import serializers

from .models import Bid, RadiologistProvider, ReadContract, TeleReadJob, TeleReport


class RadiologistProviderSerializer(serializers.ModelSerializer):
    class Meta:
        model = RadiologistProvider
        fields = "__all__"


class ReadContractSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReadContract
        fields = "__all__"


class TeleReadJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeleReadJob
        fields = "__all__"


class BidSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bid
        fields = "__all__"


class TeleReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeleReport
        fields = "__all__"
