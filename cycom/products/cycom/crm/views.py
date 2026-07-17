from core.viewsets import TenantScopedModelViewSet
from products.cycom.crm.models import Lead
from products.cycom.crm.serializers import LeadSerializer


class LeadViewSet(TenantScopedModelViewSet):
    queryset = Lead.objects.all()
    serializer_class = LeadSerializer
