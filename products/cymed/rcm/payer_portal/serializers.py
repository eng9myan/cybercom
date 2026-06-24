from rest_framework import serializers
from .models import PayerPortalAccount, PayerDashboard, PayerClaimReview, PayerAuthorizationReview


class PayerPortalAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = PayerPortalAccount
        fields = "__all__"


class PayerDashboardSerializer(serializers.ModelSerializer):
    class Meta:
        model = PayerDashboard
        fields = "__all__"


class PayerClaimReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = PayerClaimReview
        fields = "__all__"


class PayerAuthorizationReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = PayerAuthorizationReview
        fields = "__all__"
