from rest_framework import serializers

from products.cycom.referrals.models import Referral


class ReferralSerializer(serializers.ModelSerializer):
    referrer_name = serializers.CharField(source="referrer.__str__", read_only=True)

    class Meta:
        model = Referral
        fields = "__all__"
        # bonus_paid only moves via the pay-bonus action — never a raw PATCH,
        # so a referral can't be marked paid before it's actually hired.
        read_only_fields = ["id", "tenant_id", "bonus_paid", "created_at", "updated_at"]
