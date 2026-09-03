"""CyMed Pharmacy pos_insurance serializers."""
from rest_framework import serializers

from .models import (
    AdjudicationLog,
    PosSale,
    PosSaleItem,
    PosSession,
    PosTerminal,
)


class PosTerminalSerializer(serializers.ModelSerializer):
    class Meta:
        model = PosTerminal
        fields = "__all__"


class PosSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PosSession
        fields = "__all__"


class PosSaleSerializer(serializers.ModelSerializer):
    class Meta:
        model = PosSale
        fields = "__all__"


class PosSaleItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = PosSaleItem
        fields = "__all__"


class AdjudicationLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdjudicationLog
        fields = "__all__"
