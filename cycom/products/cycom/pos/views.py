from decimal import Decimal

from django.utils import timezone
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from core.viewsets import TenantScopedModelViewSet
from products.cycom.access.approvals import current_user_id, require_approval_authority
from products.cycom.access.credentials import verify_manager_credential
from products.cycom.pos.models import Device, POSOrder, POSSession, PosReceipt, PosReturn
from products.cycom.pos.serializers import (
    DeviceSerializer,
    POSOrderSerializer,
    POSSessionSerializer,
    PosReceiptSerializer,
    PosReturnSerializer,
)
from products.cycom.pos.services import (
    approve_discount,
    approve_return,
    checkout_order,
    record_payment,
    reject_discount,
    reject_return,
    submit_discount_for_approval,
    submit_return,
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

    @action(detail=True, methods=["post"], url_path="approve-discount")
    def approve_discount_action(self, request, pk=None):
        order = self.get_object()
        # HR-4/S-2 (retail): the till discount matrix (retailgroup blueprint's
        # 'pos_discount' policy: Cashier / Branch Manager / Retail Ops Manager
        # bands) governs this, not a flat platform-admin gate.
        require_approval_authority(request, order.tenant_id, "pos_discount", order.discount_amount)
        claims = getattr(request, "auth_claims", {}) or {}
        approved_by = request.data.get("approved_by", "") or claims.get("email", "")
        approve_discount(order, approved_by)
        return Response(POSOrderSerializer(order).data)

    @action(detail=True, methods=["post"], url_path="reject-discount")
    def reject_discount_action(self, request, pk=None):
        order = self.get_object()
        require_approval_authority(request, order.tenant_id, "pos_discount", order.discount_amount)
        reject_discount(order, request.data.get("reason", ""))
        return Response(POSOrderSerializer(order).data)

    @action(detail=True, methods=["post"], url_path="submit-return")
    def submit_return_action(self, request, pk=None):
        order = self.get_object()
        ret = submit_return(order, request.data.get("lines", []), request.data.get("reason", ""))
        return Response(PosReturnSerializer(ret).data, status=201)

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


def _resolve_return_approver(request, ret):
    """The pos_refund authority for this return, either from the caller's own
    role (self-service) or a manager's PIN/barcode supplied in the request
    body (till workflow — a cashier's own token lacks the role, a manager
    clears it without a full login handoff). Raises PermissionDenied if
    neither works. Returns (approved_by_user_id, approval_method)."""
    try:
        require_approval_authority(request, ret.tenant_id, "pos_refund", ret.amount_total)
        return current_user_id(request) or "", "self"
    except PermissionDenied:
        pin = request.data.get("manager_pin")
        barcode = request.data.get("manager_badge")
        manager_id = verify_manager_credential(
            ret.tenant_id, "pos_refund", ret.amount_total, pin=pin, barcode=barcode,
        )
        if manager_id:
            return manager_id, ("pin" if pin else "barcode")
        raise


class PosReturnViewSet(TenantScopedModelViewSet):
    queryset = PosReturn.objects.prefetch_related("lines").select_related("order")
    serializer_class = PosReturnSerializer
    http_method_names = ["get", "head", "options", "post"]

    def create(self, request, *args, **kwargs):
        # Real creation is POSOrderViewSet.submit-return — it needs the
        # already-returned-quantity validation a plain nested-create can't
        # express. This route only exists (vs http_method_names dropping
        # "post" entirely) so the approve/reject @actions below can POST.
        raise ValidationError(
            "Create a return via POST /api/v1/pos/orders/{id}/submit-return/, not this endpoint."
        )

    def get_queryset(self):
        qs = super().get_queryset()
        order = self.request.query_params.get("order")
        if order:
            qs = qs.filter(order=order)
        return qs

    @action(detail=True, methods=["post"], url_path="approve")
    def approve(self, request, pk=None):
        ret = self.get_object()
        approved_by_user_id, approval_method = _resolve_return_approver(request, ret)
        approve_return(ret, approved_by_user_id=approved_by_user_id, approval_method=approval_method)
        return Response(PosReturnSerializer(ret).data)

    @action(detail=True, methods=["post"], url_path="reject")
    def reject(self, request, pk=None):
        ret = self.get_object()
        # Rejecting carries no financial/stock effect — same authority bar as
        # approving is still required (a cashier shouldn't unilaterally kill
        # a colleague's return request either), so it goes through the same
        # role-or-credential check.
        _resolve_return_approver(request, ret)
        reject_return(ret, request.data.get("reason", ""))
        return Response(PosReturnSerializer(ret).data)
