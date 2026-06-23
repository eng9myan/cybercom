from rest_framework import serializers
from .models import BloodProduct, BloodInventory, BloodCompatibility, TransfusionRequest

class BloodProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = BloodProduct
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]

class BloodInventorySerializer(serializers.ModelSerializer):
    class Meta:
        model = BloodInventory
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]

class BloodCompatibilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = BloodCompatibility
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]

class TransfusionRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransfusionRequest
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]
