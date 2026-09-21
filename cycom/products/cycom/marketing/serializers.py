from rest_framework import serializers

from products.cycom.marketing.models import Campaign, MarketingRecipient


class MarketingRecipientSerializer(serializers.ModelSerializer):
    class Meta:
        model = MarketingRecipient
        fields = "__all__"
        read_only_fields = [
            "id", "tenant_id", "campaign", "status", "error_message", "sent_at",
            "created_at", "updated_at",
        ]


class CampaignSerializer(serializers.ModelSerializer):
    recipient_count = serializers.IntegerField(source="recipients.count", read_only=True)

    class Meta:
        model = Campaign
        fields = "__all__"
        read_only_fields = [
            "id", "tenant_id", "state", "sent", "failed", "created_at", "updated_at",
        ]
