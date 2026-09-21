from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from core.viewsets import TenantScopedModelViewSet
from products.cycom.marketing.models import Campaign, MarketingRecipient
from products.cycom.marketing.serializers import CampaignSerializer, MarketingRecipientSerializer
from products.cycom.marketing.services import add_recipients, send_campaign


class CampaignViewSet(TenantScopedModelViewSet):
    queryset = Campaign.objects.prefetch_related("recipients").all()
    serializer_class = CampaignSerializer
    filterset_fields = ["campaign_type", "state"]

    @action(detail=True, methods=["post"], url_path="recipients")
    def add_recipients_action(self, request, pk=None):
        campaign = self.get_object()
        contacts = request.data.get("contacts")
        if not isinstance(contacts, list) or not contacts:
            raise ValidationError("contacts must be a non-empty list.")
        created = add_recipients(campaign, contacts)
        # Not campaign.recipients.count() — the prefetch cache from
        # self.get_object() predates these inserts and Django's related
        # manager .count() reads that stale cache instead of re-querying.
        total = MarketingRecipient.objects.filter(campaign_id=campaign.id).count()
        return Response({"added": created, "total_recipients": total}, status=201)

    @action(detail=True, methods=["post"])
    def send(self, request, pk=None):
        campaign = self.get_object()
        send_campaign(campaign)
        campaign.refresh_from_db()
        return Response(CampaignSerializer(campaign).data)


class MarketingRecipientViewSet(TenantScopedModelViewSet):
    queryset = MarketingRecipient.objects.select_related("campaign").all()
    serializer_class = MarketingRecipientSerializer
    filterset_fields = ["campaign", "status"]
