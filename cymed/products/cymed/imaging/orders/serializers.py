from rest_framework import serializers

from .models import (
    ImagingOrder,
    ImagingOrderItem,
    ImagingOrderStatusHistory,
    ImagingProcedure,
    ImagingProtocol,
)


def _phi_text():
    # EncryptedText (BinaryField storage) — keep it plain text through DRF.
    return serializers.CharField(required=False, allow_blank=True)


class ImagingProtocolSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImagingProtocol
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class ImagingProcedureSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImagingProcedure
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class ImagingOrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImagingOrderItem
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class ImagingOrderStatusHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ImagingOrderStatusHistory
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at", "changed_at"]


class ImagingOrderSerializer(serializers.ModelSerializer):
    clinical_indication = _phi_text()
    items = ImagingOrderItemSerializer(many=True, read_only=True)
    status_history = ImagingOrderStatusHistorySerializer(many=True, read_only=True)

    class Meta:
        model = ImagingOrder
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]
