from django.db.models import Q
from rest_framework import viewsets
from platform.api.permissions import IsAuthenticatedClinicalStaff as IsAuthenticated  # M-7: staff-role gate

from products.cymed.core.orders.models import Order
from products.cymed.core.orders.serializers import OrderSerializer


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    # Read by the project-wide tenant filter (platform.api.tenancy) so it
    # matches get_queryset below instead of narrowing it to the owner only.
    tenant_scope_fields = ("tenant_id", "fulfilling_tenant_id")
    permission_classes = [IsAuthenticated]
    # Real consumer: Phase 9's mobile e-Rx screen filters on order_type=medication.
    filterset_fields = ["order_type", "status", "priority"]

    def get_queryset(self):
        tenant_id = getattr(self.request, "tenant_id", None)
        if not tenant_id:
            return self.queryset.none()
        # CyID ecosystem, Phase 5 — the source tenant (who wrote the
        # order) and the fulfilling tenant (who executes it, e.g. an
        # external pharmacy) both see it — a real cross-tenant order
        # queue, same pattern as Consent.granted_to_tenant_id.
        return self.queryset.filter(Q(tenant_id=tenant_id) | Q(fulfilling_tenant_id=tenant_id))
