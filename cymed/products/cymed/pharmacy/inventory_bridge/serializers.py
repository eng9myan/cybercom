from rest_framework import serializers

from .models import InventoryQueryResult, MedicationConsumptionEvent


class MedicationConsumptionEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicationConsumptionEvent
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class InventoryQueryResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = InventoryQueryResult
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at", "cached_at"]
