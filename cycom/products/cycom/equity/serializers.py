from rest_framework import serializers

from products.cycom.equity.models import (
    DividendAllocation,
    DividendDistribution,
    ShareClass,
    ShareGrant,
    Shareholder,
)


class ShareClassSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShareClass
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]

    def validate(self, attrs):
        class_type = attrs.get("class_type", getattr(self.instance, "class_type", None))
        pref = attrs.get(
            "liquidation_preference_multiple",
            getattr(self.instance, "liquidation_preference_multiple", None),
        )
        if class_type == "common" and pref:
            raise serializers.ValidationError("Common stock cannot have a liquidation preference.")
        return attrs


class ShareholderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shareholder
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class ShareGrantSerializer(serializers.ModelSerializer):
    vested_quantity = serializers.SerializerMethodField()

    class Meta:
        model = ShareGrant
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]

    def get_vested_quantity(self, obj):
        from django.utils import timezone

        return str(obj.vested_quantity(timezone.now().date()))


class DividendAllocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = DividendAllocation
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class DividendDistributionSerializer(serializers.ModelSerializer):
    allocations = DividendAllocationSerializer(many=True, read_only=True)

    class Meta:
        model = DividendDistribution
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at", "status"]
