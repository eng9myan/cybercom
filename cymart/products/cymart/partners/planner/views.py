from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ..auth import PartnerAPIKeyAuthentication
from ..models import PartnerCallLog
from .basket import build_basket
from .serializers import BasketRequestSerializer, TargetsRequestSerializer, WeekRequestSerializer
from .targets import build_targets
from .weekly import plan_week


class _PlannerView(APIView):
    authentication_classes = [PartnerAPIKeyAuthentication]
    permission_classes = [IsAuthenticated]
    request_serializer = None

    def parse(self, request):
        s = self.request_serializer(data=request.data)
        s.is_valid(raise_exception=True)
        return s.validated_data

    @staticmethod
    def meter(request, n):
        PartnerCallLog.objects.create(partner=request.partner, item_count=min(n, 32000))


class PlanTargetsView(_PlannerView):
    """Plan setup: a person's details -> daily calories, macros, per-meal budgets and a shield profile."""
    request_serializer = TargetsRequestSerializer

    def post(self, request):
        data = self.parse(request)
        out = build_targets(data["intake"], data["language"])
        self.meter(request, 0)
        return Response(out)


class PlanWeekView(_PlannerView):
    """A shield-checked week of meals from the platform's own items, with runners-up for each meal."""
    request_serializer = WeekRequestSerializer

    def post(self, request):
        data = self.parse(request)
        out = plan_week(data["shield_profile"], data["per_meal"], data["pool"], days=data["days"],
                        slots=tuple(data["slots"]), lang=data["language"])
        self.meter(request, len(data["pool"]))
        return Response(out)


class PlanBasketView(_PlannerView):
    """A shield-checked weekly grocery basket from the platform's own grocery items."""
    request_serializer = BasketRequestSerializer

    def post(self, request):
        data = self.parse(request)
        out = build_basket(data["shield_profile"], data["pool"], data["weekly_calories"], data["needs"], data["language"])
        self.meter(request, len(data["pool"]))
        return Response(out)
