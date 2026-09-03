from core.viewsets import TenantScopedModelViewSet
from products.cycom.marketing.models import Campaign
from products.cycom.marketing.serializers import CampaignSerializer


class CampaignViewSet(TenantScopedModelViewSet):
    queryset = Campaign.objects.all()
    serializer_class = CampaignSerializer
