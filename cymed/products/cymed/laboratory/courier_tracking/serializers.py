"""DRF serializers for CyMed Laboratory courier tracking models."""

from __future__ import annotations

from rest_framework import serializers

from .models import ChainOfCustodyEvent, Manifest, Route, Run, TransportTemperature


class RouteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Route
        fields = "__all__"


class RunSerializer(serializers.ModelSerializer):
    class Meta:
        model = Run
        fields = "__all__"


class ChainOfCustodyEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChainOfCustodyEvent
        fields = "__all__"


class TransportTemperatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransportTemperature
        fields = "__all__"


class ManifestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Manifest
        fields = "__all__"
