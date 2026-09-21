from core.viewsets import TenantScopedModelViewSet
from products.cycom.helpdesk.models import SLAPolicy, Ticket
from products.cycom.helpdesk.serializers import SLAPolicySerializer, TicketSerializer


class SLAPolicyViewSet(TenantScopedModelViewSet):
    queryset = SLAPolicy.objects.all()
    serializer_class = SLAPolicySerializer
    filterset_fields = ["team", "priority", "is_active"]


class TicketViewSet(TenantScopedModelViewSet):
    queryset = Ticket.objects.select_related("sla_policy").all()
    serializer_class = TicketSerializer
    filterset_fields = ["stage", "priority", "team"]
