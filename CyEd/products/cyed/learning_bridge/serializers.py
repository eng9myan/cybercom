from rest_framework import serializers

from products.cyed.learning_bridge.models import FamilyResource, OfflineActivityPack


class FamilyResourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = FamilyResource
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_by", "created_at", "updated_at"]


class OfflineActivityPackSerializer(serializers.ModelSerializer):
    class Meta:
        model = OfflineActivityPack
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "approved_by", "created_at", "updated_at"]
