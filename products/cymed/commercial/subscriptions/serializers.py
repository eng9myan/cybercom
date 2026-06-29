from rest_framework import serializers

from products.cymed.commercial.subscriptions.models import (
    Subscription,
    SubscriptionContract,
    SubscriptionInvoice,
    SubscriptionPlan,
    SubscriptionUsage,
)


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = "__all__"


class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = "__all__"


class SubscriptionUsageSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionUsage
        fields = "__all__"


class SubscriptionInvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionInvoice
        fields = "__all__"


class SubscriptionContractSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionContract
        fields = "__all__"
