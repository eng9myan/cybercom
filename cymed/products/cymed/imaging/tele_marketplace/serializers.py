"""DRF serializers for teleradiology marketplace resources."""

from __future__ import annotations

from rest_framework import serializers

from .models import Bid, RadiologistProvider, ReadContract, TeleReadJob, TeleReport


def _phi_text():
    # EncryptedText (BinaryField storage) — keep it plain text through DRF.
    return serializers.CharField(required=False, allow_blank=True)


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
    text = _phi_text()
    impressions = _phi_text()

    class Meta:
        model = TeleReport
        fields = "__all__"
