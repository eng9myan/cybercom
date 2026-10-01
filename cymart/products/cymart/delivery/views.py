from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from products.cymart.orders.models import MarketplaceOrder

from .models import DeliveryAssignment, DeliveryRun
from .serializers import (
    AssignBatchRequestSerializer,
    AssignDriverRequestSerializer,
    OrderTrackingSerializer,
    RecordEventRequestSerializer,
    RunStatusSerializer,
    ZoneCheckRequestSerializer,
)
from .services import (
    DispatchService,
    NoDriverAvailableError,
    OrderAlreadyAssignedError,
    TrackingService,
    ZoneService,
)


class ZoneCheckView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = ZoneCheckRequestSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        zone = ZoneService().is_deliverable(
            serializer.validated_data["lat"], serializer.validated_data["lng"]
        )
        if zone is None:
            return Response({"deliverable": False})
        return Response({"deliverable": True, "zone": zone.name, "city": zone.city})


class AssignDriverView(APIView):
    """Dispatch — called by the ops/merchant side once an order is ready
    to go out. Not customer-facing (no ownership check here; that's an
    ops-role concern for a later auth pass)."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AssignDriverRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            order = MarketplaceOrder.objects.get(id=data["order_id"])
        except MarketplaceOrder.DoesNotExist:
            return Response({"detail": "Order not found."}, status=404)

        try:
            assignment = DispatchService().assign_nearest_driver(
                order, data["store_lat"], data["store_lng"]
            )
        except (NoDriverAvailableError, OrderAlreadyAssignedError) as exc:
            return Response({"detail": str(exc)}, status=409)
        return Response(
            {"assignment_id": assignment.id, "driver": assignment.driver.name, "status": assignment.status},
            status=201,
        )


class AssignBatchView(APIView):
    """Dispatch one driver to cover several orders in one trip — e.g. the
    customer ordered food from one restaurant and groceries from another
    merchant; one courier picks up both instead of two separate ones."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AssignBatchRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        legs_data = serializer.validated_data["legs"]

        order_ids = [leg["order_id"] for leg in legs_data]
        orders = {o.id: o for o in MarketplaceOrder.objects.filter(id__in=order_ids)}
        missing = [str(oid) for oid in order_ids if oid not in orders]
        if missing:
            return Response({"detail": f"Order(s) not found: {', '.join(missing)}"}, status=404)

        legs = [(orders[leg["order_id"]], leg["store_lat"], leg["store_lng"]) for leg in legs_data]
        try:
            run = DispatchService().assign_batch(legs)
        except (NoDriverAvailableError, OrderAlreadyAssignedError) as exc:
            return Response({"detail": str(exc)}, status=409)
        return Response(RunStatusSerializer(TrackingService().status_for_run(run)).data, status=201)


class RunStatusView(APIView):
    """The driver-facing view of a batched trip — every stop it covers."""

    permission_classes = [IsAuthenticated]

    def get(self, request, run_id):
        try:
            run = DeliveryRun.objects.get(id=run_id)
        except DeliveryRun.DoesNotExist:
            return Response({"detail": "Run not found."}, status=404)
        return Response(RunStatusSerializer(TrackingService().status_for_run(run)).data)


class RecordTrackingEventView(APIView):
    """Called by the driver app as the order moves — picked up, arriving,
    delivered."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = RecordEventRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        assignment = (
            DeliveryAssignment.objects.filter(order_id=data["order_id"])
            .order_by("-assigned_at")
            .first()
        )
        if assignment is None:
            return Response({"detail": "No delivery assignment for this order."}, status=404)
        event = TrackingService().record_event(assignment, data["status"], data.get("note", ""))
        return Response({"status": event.status, "occurred_at": event.occurred_at}, status=201)


class OrderTrackingView(APIView):
    """The customer-facing live-tracking read — scoped to the caller's
    own order."""

    permission_classes = [IsAuthenticated]

    def get(self, request, order_id):
        customer_id = request.user_session["user_id"]
        try:
            order = MarketplaceOrder.objects.get(id=order_id, customer_id=customer_id)
        except MarketplaceOrder.DoesNotExist:
            return Response({"detail": "Order not found."}, status=404)

        status_info = TrackingService().status_for_order(order)
        if status_info is None:
            return Response({"detail": "No driver assigned yet."}, status=404)
        return Response(OrderTrackingSerializer(status_info).data)
