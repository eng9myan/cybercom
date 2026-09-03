"""DRF serializers for the DTC test catalog models."""
from __future__ import annotations

from rest_framework import serializers

from .models import DtcCategory, DtcKit, DtcOrder, DtcProduct


class DtcCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = DtcCategory
        fields = "__all__"


class DtcProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = DtcProduct
        fields = "__all__"


class DtcKitSerializer(serializers.ModelSerializer):
    class Meta:
        model = DtcKit
        fields = "__all__"


class DtcOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = DtcOrder
        fields = "__all__"
