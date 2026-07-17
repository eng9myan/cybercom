from decimal import Decimal

from django.utils import timezone
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from core.viewsets import TenantScopedModelViewSet
from products.cycom.pos.models import POSOrder, POSSession
from products.cycom.pos.serializers import POSOrderSerializer, POSSessionSerializer
from products.cycom.pos.services import checkout_order


class POSSessionViewSet(TenantScopedModelViewSet):
    queryset = POSSession.objects.all()
    serializer_class = POSSessionSerializer

    @action(detail=True, methods=["post"], url_path="close")
    def close(self, request, pk=None):
        session = self.get_object()
        if session.status != "open":
            raise ValidationError(f"Session is already '{session.status}'.")
        closing_cash = request.data.get("closing_cash")
        if closing_cash is None:
            raise ValidationError("closing_cash is required.")
        closing_cash = Decimal(str(closing_cash))

        cash_sales = sum(
            (o.amount_total for o in session.orders.filter(status="paid")), Decimal("0")
        )
        expected_cash = session.opening_cash + cash_sales

        session.closing_cash = closing_cash
        session.status = "closed"
        session.closed_at = timezone.now()
        session.save(update_fields=["closing_cash", "status", "closed_at"])

        return Response(
            {
                **POSSessionSerializer(session).data,
                "expected_cash": str(expected_cash),
                "variance": str(closing_cash - expected_cash),
            }
        )


class POSOrderViewSet(TenantScopedModelViewSet):
    queryset = POSOrder.objects.prefetch_related("lines").all()
    serializer_class = POSOrderSerializer

    @action(detail=True, methods=["post"], url_path="checkout")
    def checkout(self, request, pk=None):
        order = self.get_object()
        checkout_order(order)
        return Response(POSOrderSerializer(order).data)
