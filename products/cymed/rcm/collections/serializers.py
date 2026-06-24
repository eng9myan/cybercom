from rest_framework import serializers
from .models import CollectionCase, CollectionAction, PaymentPlan, CollectionOutcome


class CollectionCaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = CollectionCase
        fields = "__all__"


class CollectionActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CollectionAction
        fields = "__all__"


class PaymentPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentPlan
        fields = "__all__"


class CollectionOutcomeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CollectionOutcome
        fields = "__all__"
