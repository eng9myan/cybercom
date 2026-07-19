from rest_framework import serializers

from products.cycom.subscriptions.models import Subscription, SubscriptionPlan


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]


class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = "__all__"
        read_only_fields = [
            "id", "tenant_id", "created_at", "updated_at",
            "status", "next_billing_date", "cancelled_at",
        ]

    def create(self, validated_data):
        validated_data.setdefault("next_billing_date", validated_data.get("start_date"))
        return super().create(validated_data)
