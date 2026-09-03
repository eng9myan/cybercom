from rest_framework import serializers

from products.cycom.marketing.models import Campaign


class CampaignSerializer(serializers.ModelSerializer):
    class Meta:
        model = Campaign
        fields = "__all__"
        read_only_fields = ["id", "tenant_id", "created_at", "updated_at"]
