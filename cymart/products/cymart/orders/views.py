from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import MarketplaceOrder
from .serializers import MarketplaceOrderSerializer
from .services import InvalidOrderTransitionError, OrderStateMachine


class MarketplaceOrderViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only + a transition action — orders are created through
    OrderService.create_order() (checkout flow), not raw POST, since
    creation has to be idempotent and compute totals server-side.
    """

    serializer_class = MarketplaceOrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = MarketplaceOrder.objects.all().order_by("-created_at")
        tenant_id = self.request.query_params.get("tenant_id")
        customer_id = self.request.query_params.get("customer_id")
        status_param = self.request.query_params.get("status")
        if tenant_id:
            qs = qs.filter(tenant_id=tenant_id)
        if customer_id:
            qs = qs.filter(customer_id=customer_id)
        if status_param:
            qs = qs.filter(status=status_param)
        return qs

    @action(detail=True, methods=["post"])
    def transition(self, request, pk=None):
        order = self.get_object()
        to_status = request.data.get("to_status")
        reason = request.data.get("reason", "")
        try:
            order = OrderStateMachine().transition(order, to_status, reason=reason)
        except InvalidOrderTransitionError as exc:
            return Response({"detail": str(exc)}, status=400)
        return Response(self.get_serializer(order).data)
