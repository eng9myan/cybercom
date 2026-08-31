from decimal import Decimal

from django.utils import timezone
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from core.viewsets import TenantScopedModelViewSet
from platform.tenant.permissions import IsPlatformAdmin
from products.cycom.pos.models import Device, POSOrder, POSSession, PosReceipt
from products.cycom.pos.serializers import (
    DeviceSerializer,
    POSOrderSerializer,
    POSSessionSerializer,
    PosReceiptSerializer,
)
from products.cycom.pos.services import (
    approve_discount,
    checkout_order,
    record_payment,
    reject_discount,
    submit_discount_for_approval,
)


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

    @action(detail=True, methods=["post"], url_path="submit-discount")
    def submit_discount(self, request, pk=None):
        order = self.get_object()
        submit_discount_for_approval(order)
        return Response(POSOrderSerializer(order).data)

    @action(
        detail=True, methods=["post"], url_path="approve-discount", permission_classes=[IsPlatformAdmin]
    )
    def approve_discount_action(self, request, pk=None):
        order = self.get_object()
        claims = getattr(request, "auth_claims", {}) or {}
        approved_by = request.data.get("approved_by", "") or claims.get("email", "")
        approve_discount(order, approved_by)
        return Response(POSOrderSerializer(order).data)

    @action(
        detail=True, methods=["post"], url_path="reject-discount", permission_classes=[IsPlatformAdmin]
    )
    def reject_discount_action(self, request, pk=None):
        order = self.get_object()
        reject_discount(order, request.data.get("reason", ""))
        return Response(POSOrderSerializer(order).data)

    @action(detail=True, methods=["post"], url_path="add-payment")
    def add_payment(self, request, pk=None):
        order = self.get_object()
        amount = request.data.get("amount")
        amount = Decimal(str(amount)) if amount is not None else None
        record_payment(order, amount, request.data.get("method", "cash"))
        return Response(POSOrderSerializer(order).data)

    @action(detail=False, methods=["get"], url_path="kds")
    def kds(self, request):
        """
        Kitchen-display feed: open tickets not yet served, oldest first.
        Optional ?kitchen_status= filters to a single lane.
        """
        qs = self.get_queryset().exclude(kitchen_status="served").order_by("created_at")
        ks = request.query_params.get("kitchen_status")
        if ks:
            qs = qs.filter(kitchen_status=ks)
        return Response(POSOrderSerializer(qs, many=True).data)

    @action(detail=True, methods=["post"], url_path="kitchen-status")
    def kitchen_status(self, request, pk=None):
        """
        Set the kitchen ticket stage. Body {"kitchen_status": "..."} sets it
        explicitly; {"advance": true} steps one stage forward.
        """
        order = self.get_object()
        if request.data.get("advance"):
            order.advance_kitchen()
        else:
            target = request.data.get("kitchen_status")
            valid = dict(POSOrder.KITCHEN_STATUS_CHOICES)
            if target not in valid:
                raise ValidationError(f"kitchen_status must be one of {list(valid)}.")
            order.kitchen_status = target
            order.save(update_fields=["kitchen_status", "updated_at"])
        return Response(POSOrderSerializer(order).data)


class DeviceViewSet(TenantScopedModelViewSet):
    queryset = Device.objects.all().select_related("warehouse")
    serializer_class = DeviceSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        dt = self.request.query_params.get("device_type")
        if dt:
            qs = qs.filter(device_type=dt)
        wh = self.request.query_params.get("warehouse")
        if wh:
            qs = qs.filter(warehouse=wh)
        return qs

    @action(detail=True, methods=["post"], url_path="heartbeat")
    def heartbeat(self, request, pk=None):
        """A live terminal/display pings this to update last_seen_at."""
        device = self.get_object()
        device.last_seen_at = timezone.now()
        device.save(update_fields=["last_seen_at", "updated_at"])
        return Response(self.get_serializer(device).data)


class PosReceiptViewSet(TenantScopedModelViewSet):
    queryset = PosReceipt.objects.all().select_related("order")
    serializer_class = PosReceiptSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        order = self.request.query_params.get("order")
        if order:
            qs = qs.filter(order=order)
        return qs
