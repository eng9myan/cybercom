from rest_framework.views import APIView

from core.permissions import IsAuthenticatedViaClaims
from core.viewsets import TenantScopedModelViewSet
from products.cyed.governance.access import IsStaff, scope_queryset_by_student
from products.cyed.transport.models import (
    Bus,
    CustomStop,
    RfidBoardingEvent,
    TransportSubscription,
    TransportZone,
)
from products.cyed.transport.serializers import (
    BusSerializer,
    CustomStopSerializer,
    RfidBoardingEventSerializer,
    TransportSubscriptionSerializer,
    TransportZoneSerializer,
)


class TransportZoneViewSet(TenantScopedModelViewSet):
    queryset = TransportZone.objects.all()
    serializer_class = TransportZoneSerializer
    permission_classes = [IsStaff]


class BusViewSet(TenantScopedModelViewSet):
    queryset = Bus.objects.all()
    serializer_class = BusSerializer
    permission_classes = [IsStaff]


class TransportSubscriptionViewSet(TenantScopedModelViewSet):
    queryset = TransportSubscription.objects.select_related("student", "zone", "assigned_bus").all()
    serializer_class = TransportSubscriptionSerializer

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [IsAuthenticatedViaClaims()]
        return [IsStaff()]

    def get_queryset(self):
        qs = super().get_queryset()
        qs = scope_queryset_by_student(self.request, self.request.tenant_id, qs, student_path="student_id")
        student = self.request.query_params.get("student")
        bus = self.request.query_params.get("bus")
        if student:
            qs = qs.filter(student_id=student)
        if bus:
            qs = qs.filter(assigned_bus_id=bus)
        return qs

    def perform_create(self, serializer):
        obj = serializer.save(tenant_id=self.request.tenant_id)
        obj.fee_amount = obj.compute_fee()
        obj.save(update_fields=["fee_amount", "updated_at"])

    def perform_update(self, serializer):
        obj = serializer.save()
        recomputed = obj.compute_fee()
        if recomputed != obj.fee_amount:
            obj.fee_amount = recomputed
            obj.save(update_fields=["fee_amount", "updated_at"])
        # Keep any linked bill in sync when transport changes mid-year.
        _sync_bill_for_student(obj.tenant_id, obj.student_id)


def _sync_bill_for_student(tenant_id, student_id):
    try:
        from products.cyed.billing.services import resync_transport_line

        resync_transport_line(tenant_id, student_id)
    except Exception:
        pass


class CustomStopViewSet(TenantScopedModelViewSet):
    queryset = CustomStop.objects.select_related("subscription").all()
    serializer_class = CustomStopSerializer
    permission_classes = [IsStaff]

    def get_queryset(self):
        qs = super().get_queryset()
        subscription = self.request.query_params.get("subscription")
        if subscription:
            qs = qs.filter(subscription_id=subscription)
        return qs


class RfidBoardingEventViewSet(TenantScopedModelViewSet):
    queryset = RfidBoardingEvent.objects.select_related("student", "bus").all()
    serializer_class = RfidBoardingEventSerializer

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [IsAuthenticatedViaClaims()]
        return [IsStaff()]  # posted by staff / the reader's service account

    def get_queryset(self):
        qs = super().get_queryset()
        qs = scope_queryset_by_student(self.request, self.request.tenant_id, qs, student_path="student_id")
        student = self.request.query_params.get("student")
        if student:
            qs = qs.filter(student_id=student)
        return qs


# ── GPS live tracking + route optimization ──────────────────────────────────
from django.utils import timezone as _tz  # noqa: E402
from rest_framework import status as _status  # noqa: E402
from rest_framework.decorators import action as _action  # noqa: E402
from rest_framework.response import Response as _Response  # noqa: E402

from products.cyed.transport.models import BusLocation, BusRoute, RouteStop  # noqa: E402
from products.cyed.transport import routing as _routing  # noqa: E402
from products.cyed.transport.serializers import (  # noqa: E402
    BusLocationSerializer,
    BusRouteSerializer,
    RouteStopSerializer,
)


def _parent_may_see_bus(request, tenant_id, bus_id) -> bool:
    """A parent/student may see the live bus their child/self is subscribed to."""
    from products.cyed.governance.access import is_staff, visible_student_ids

    if is_staff(request):
        return True
    visible = visible_student_ids(request, tenant_id)
    if visible is None:
        return True
    return TransportSubscription.objects.filter(
        tenant_id=tenant_id, student_id__in=visible, assigned_bus_id=bus_id
    ).exists()


class BusRouteViewSet(TenantScopedModelViewSet):
    queryset = BusRoute.objects.prefetch_related("stops").select_related("bus").all()
    serializer_class = BusRouteSerializer
    permission_classes = [IsStaff]

    @_action(detail=True, methods=["post"])
    def optimize(self, request, pk=None):
        route = self.get_object()
        stops = [{"id": str(s.id), "name": s.name, "lat": s.lat, "lng": s.lng}
                 for s in route.stops.all()]
        ordered, total = _routing.optimize_order(stops)
        for i, s in enumerate(ordered, start=1):
            RouteStop.objects.filter(id=s["id"]).update(sequence=i)
        route.total_distance_km = total
        route.save(update_fields=["total_distance_km", "updated_at"])
        return _Response(self.get_serializer(route).data)


class RouteStopViewSet(TenantScopedModelViewSet):
    queryset = RouteStop.objects.select_related("route").all()
    serializer_class = RouteStopSerializer
    permission_classes = [IsStaff]

    def get_queryset(self):
        qs = super().get_queryset()
        route = self.request.query_params.get("route")
        if route:
            qs = qs.filter(route_id=route)
        return qs


class BusLocationViewSet(TenantScopedModelViewSet):
    """
    POST create = a GPS ping from the on-bus device (staff/service credential).
    GET list = recent pings. See `BusLiveView` for the parent-facing live+ETA.
    """

    queryset = BusLocation.objects.select_related("bus").all()
    serializer_class = BusLocationSerializer

    def get_permissions(self):
        if self.action == "create":
            return [IsStaff()]  # device/service account posts telemetry
        return [IsAuthenticatedViaClaims()]

    def get_queryset(self):
        qs = super().get_queryset()
        bus = self.request.query_params.get("bus")
        if bus:
            qs = qs.filter(bus_id=bus)
        return qs

    def perform_create(self, serializer):
        serializer.save(tenant_id=self.request.tenant_id, recorded_at=_tz.now())


class BusLiveView(APIView):
    """GET /api/v1/transport/buses/<bus_id>/live/ → latest position + ETAs (parent-scoped)."""

    permission_classes = [IsAuthenticatedViaClaims]

    def get(self, request, bus_id):
        tenant_id = getattr(request, "tenant_id", None)
        if tenant_id is None:
            return _Response({"detail": "A tenant context is required."}, status=_status.HTTP_400_BAD_REQUEST)
        if not _parent_may_see_bus(request, tenant_id, bus_id):
            return _Response({"detail": "Not permitted for this bus."}, status=_status.HTTP_403_FORBIDDEN)
        loc = BusLocation.objects.filter(tenant_id=tenant_id, bus_id=bus_id).order_by("-created_at").first()
        route = BusRoute.objects.filter(tenant_id=tenant_id, bus_id=bus_id, is_active=True).first()
        etas = []
        if loc and route:
            stops = [{"id": str(s.id), "name": s.name, "lat": s.lat, "lng": s.lng}
                     for s in route.stops.all().order_by("sequence")]
            etas = _routing.eta_minutes(loc.lat, loc.lng, stops,
                                        avg_speed_kmh=float(loc.speed_kmh) or 30.0)
        return _Response({
            "bus": str(bus_id),
            "location": BusLocationSerializer(loc).data if loc else None,
            "route": BusRouteSerializer(route).data if route else None,
            "etas": etas,
        })
