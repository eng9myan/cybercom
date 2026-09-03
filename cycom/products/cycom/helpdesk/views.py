from core.viewsets import TenantScopedModelViewSet
from products.cycom.helpdesk.models import Ticket
from products.cycom.helpdesk.serializers import TicketSerializer


class TicketViewSet(TenantScopedModelViewSet):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer
    filterset_fields = ["stage", "priority", "team"]
