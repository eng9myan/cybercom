from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .. import schema  # noqa: F401
from ..auth import PartnerAPIKeyAuthentication
from ..metering import record_usage
from ..throttle import PartnerRateThrottle
from .basket import build_basket
from .serializers import BasketRequestSerializer, TargetsRequestSerializer, WeekRequestSerializer
from .targets import build_targets
from .weekly import plan_week


class _PlannerView(APIView):
    authentication_classes = [PartnerAPIKeyAuthentication]
    permission_classes = [IsAuthenticated]
    throttle_classes = [PartnerRateThrottle]
    request_serializer = None

    def parse(self, request):
        s = self.request_serializer(data=request.data)
        s.is_valid(raise_exception=True)
        return s.validated_data

    @staticmethod
    def meter(request, n):
        record_usage(request.partner, n)


class PlanTargetsView(_PlannerView):
    """Plan setup: a person's details -> daily calories, macros, per-meal budgets and a shield profile."""
    request_serializer = TargetsRequestSerializer

    @extend_schema(request=TargetsRequestSerializer, responses={200: OpenApiTypes.OBJECT, 400: OpenApiTypes.OBJECT, 403: OpenApiTypes.OBJECT, 429: OpenApiTypes.OBJECT},
                   summary="Plan setup", description="A person's details become a daily calorie target, macros, a budget for each meal and a shield profile. Adults only; safety limits built in.")
    def post(self, request):
        data = self.parse(request)
        out = build_targets(data["intake"], data["language"])
        self.meter(request, 0)
        return Response(out)


class PlanWeekView(_PlannerView):
    """A shield-checked week of meals from the platform's own items, with runners-up for each meal."""
    request_serializer = WeekRequestSerializer

    @extend_schema(request=WeekRequestSerializer, responses={200: OpenApiTypes.OBJECT, 400: OpenApiTypes.OBJECT, 403: OpenApiTypes.OBJECT, 429: OpenApiTypes.OBJECT},
                   summary="Weekly meal plan", description="A shield-checked week of meals from your own items, with two runners-up per meal. Only items that fully fit are planned.")
    def post(self, request):
        data = self.parse(request)
        out = plan_week(data["shield_profile"], data["per_meal"], data["pool"], days=data["days"],
                        slots=tuple(data["slots"]), lang=data["language"])
        self.meter(request, len(data["pool"]))
        return Response(out)


class PlanBasketView(_PlannerView):
    """A shield-checked weekly grocery basket from the platform's own grocery items."""
    request_serializer = BasketRequestSerializer

    @extend_schema(request=BasketRequestSerializer, responses={200: OpenApiTypes.OBJECT, 400: OpenApiTypes.OBJECT, 403: OpenApiTypes.OBJECT, 429: OpenApiTypes.OBJECT},
                   summary="Weekly grocery basket", description="A shield-checked basket by food group from your own grocery items, re-checked as one basket against the week's calories.")
    def post(self, request):
        data = self.parse(request)
        out = build_basket(data["shield_profile"], data["pool"], data["weekly_calories"], data["needs"], data["language"])
        self.meter(request, len(data["pool"]))
        return Response(out)
