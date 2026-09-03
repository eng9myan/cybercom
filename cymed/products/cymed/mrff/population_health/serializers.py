"""DRF serializers for CyMed MRFF population health models."""
from __future__ import annotations

from rest_framework import serializers

from .models import (
    OutbreakModel,
    PopulationCohort,
    PopulationMetric,
    Registry,
    RegistryCase,
    TreatmentComparator,
)


class RegistrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Registry
        fields = "__all__"


class RegistryCaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegistryCase
        fields = "__all__"


class PopulationCohortSerializer(serializers.ModelSerializer):
    class Meta:
        model = PopulationCohort
        fields = "__all__"


class PopulationMetricSerializer(serializers.ModelSerializer):
    class Meta:
        model = PopulationMetric
        fields = "__all__"


class OutbreakModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = OutbreakModel
        fields = "__all__"


class TreatmentComparatorSerializer(serializers.ModelSerializer):
    class Meta:
        model = TreatmentComparator
        fields = "__all__"
