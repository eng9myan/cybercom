from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import DietRegime
from .serializers import (
    DietPlanSerializer,
    DietProfileSerializer,
    DietRegimeSerializer,
    EvaluateRequestSerializer,
    LineVerdictSerializer,
)
from .services import DietDayService, ProfileService, ShieldGate


def _customer_id(request):
    """The caller's id from the verified JWT — never a client param, so a
    client can't read or write another customer's diet profile."""
    return request.user_session["user_id"]


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = ProfileService().get(_customer_id(request))
        if profile is None:
            return Response({"detail": "No diet profile yet."}, status=404)
        return Response(DietProfileSerializer(profile).data)

    def post(self, request):
        serializer = DietProfileSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = dict(serializer.validated_data)
        regime_codes = data.pop("regime_codes", None)
        profile, plan = ProfileService().upsert(
            _customer_id(request), data, regime_codes=regime_codes
        )
        return Response(
            {
                "profile": DietProfileSerializer(profile).data,
                "plan": DietPlanSerializer(plan).data,
            },
            status=status.HTTP_201_CREATED,
        )


class PlanView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        svc = ProfileService()
        profile = svc.get(_customer_id(request))
        if profile is None:
            return Response({"detail": "No diet profile yet."}, status=404)
        plan = svc.active_plan(profile)
        if plan is None:
            return Response({"detail": "No active plan."}, status=404)
        return Response(DietPlanSerializer(plan).data)


class RegimeListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        regimes = DietRegime.objects.filter(is_active=True)
        return Response(DietRegimeSerializer(regimes, many=True).data)


class TodayView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        svc = ProfileService()
        profile = svc.get(_customer_id(request))
        if profile is None:
            return Response({"detail": "No diet profile yet."}, status=404)
        plan = svc.active_plan(profile)
        if plan is None:
            return Response({"detail": "No active plan."}, status=404)
        return Response(DietDayService().status(profile, plan))


class EvaluateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        req = EvaluateRequestSerializer(data=request.data)
        req.is_valid(raise_exception=True)
        items = [
            {"product_id": i["product_id"], "quantity": i["quantity"]}
            for i in req.validated_data["items"]
        ]
        result = ShieldGate().evaluate_items(_customer_id(request), items)
        if result is None:
            return Response({"shield_active": False, "overall": "ALLOW", "lines": []})
        return Response(
            {
                "shield_active": True,
                "overall": result.overall.name,
                "allowed": result.allowed,
                "remaining_calories_before": int(result.remaining_calories_before),
                "projected_calories_after": int(result.projected_calories_after),
                "lines": LineVerdictSerializer(result.lines, many=True).data,
            }
        )
