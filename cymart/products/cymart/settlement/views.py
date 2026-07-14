from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import SettlementLedgerEntry
from .serializers import SettlementLedgerEntrySerializer


class SettlementLedgerEntryViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = SettlementLedgerEntrySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = SettlementLedgerEntry.objects.all().order_by("-created_at")
        tenant_id = self.request.query_params.get("tenant_id")
        order_id = self.request.query_params.get("order_id")
        if tenant_id:
            qs = qs.filter(tenant_id=tenant_id)
        if order_id:
            qs = qs.filter(order_id=order_id)
        return qs
