from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from . import schema  # noqa: F401  (registers the API-key scheme for the docs)
from .auth import PartnerAPIKeyAuthentication
from .engine import PartnerShieldEngine
from .metering import record_usage
from .prepare import KitchenInstructions
from .ranking import PartnerRanker
from .throttle import PartnerRateThrottle
from .serializers import PartnerEvaluateRequestSerializer, PartnerRankRequestSerializer, PartnerPrepareRequestSerializer


class PartnerEvaluateView(APIView):
    """The whole product: send item and user data inline, get a verdict
    back. The only side effect is a usage-metering log row."""

    authentication_classes = [PartnerAPIKeyAuthentication]
    permission_classes = [IsAuthenticated]
    throttle_classes = [PartnerRateThrottle]

    @extend_schema(request=PartnerEvaluateRequestSerializer, responses={200: OpenApiTypes.OBJECT, 400: OpenApiTypes.OBJECT, 403: OpenApiTypes.OBJECT, 429: OpenApiTypes.OBJECT},
                   summary="Check items against a customer's plan", description="Allergies (always a hard block), diet rules and the calorie budget, per item or per basket. Returns allow / warn / block with a reason code, and a swap from the alternatives you send.")
    def post(self, request):
        serializer = PartnerEvaluateRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        result = PartnerShieldEngine(data["language"]).evaluate(
            data["profile"], data["items"], cumulative=data["cumulative"]
        )
        record_usage(request.partner, len(data["items"]))

        return Response(
            {
                "language": data["language"],
                "overall": result.overall,
                "allowed": result.allowed,
                "lines": [
                    {
                        "item_id": ln.item_id,
                        "severity": ln.severity,
                        "code": ln.code,
                        "reason": ln.reason,
                        "matched": ln.matched,
                        "allowed": ln.allowed,
                        "swap": ln.swap,
                    }
                    for ln in result.lines
                ],
            }
        )


class PartnerRankView(APIView):
    """Filter and rank: send many candidate items (what your own search
    returned), get back only those that fit the plan, best fit first."""

    authentication_classes = [PartnerAPIKeyAuthentication]
    permission_classes = [IsAuthenticated]
    throttle_classes = [PartnerRateThrottle]

    @extend_schema(request=PartnerRankRequestSerializer, responses={200: OpenApiTypes.OBJECT, 400: OpenApiTypes.OBJECT, 403: OpenApiTypes.OBJECT, 429: OpenApiTypes.OBJECT},
                   summary="Filter and rank search results", description="Send what your own search returned; get back only the items that fit the plan, best fit first, plus a reason code for everything hidden.")
    def post(self, request):
        serializer = PartnerRankRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        result = PartnerRanker(data["language"]).rank(
            data["profile"], data["items"], limit=data["limit"],
            include_warnings=data["include_warnings"],
        )
        record_usage(request.partner, len(data["items"]))

        return Response(
            {
                "language": data["language"],
                "counts": {
                    "evaluated": result.evaluated,
                    "fit": result.fit,
                    "fit_with_warning": result.warned,
                    "excluded": len(result.excluded),
                },
                "ranked": [
                    {
                        "rank": r.rank,
                        "item_id": r.item_id,
                        "severity": r.severity,
                        "code": r.code,
                        "reason": r.reason,
                        "fit_score": r.fit_score,
                        "relevance": r.relevance,
                        "summary": r.summary,
                        "detail": r.detail,
                    }
                    for r in result.ranked
                ],
                "excluded": result.excluded,
            }
        )


class PartnerPrepareView(APIView):
    """Kitchen instructions: after the customer picks items, turn their plan
    into the requirements the vendor must follow for this order."""

    authentication_classes = [PartnerAPIKeyAuthentication]
    permission_classes = [IsAuthenticated]
    throttle_classes = [PartnerRateThrottle]

    @extend_schema(request=PartnerPrepareRequestSerializer, responses={200: OpenApiTypes.OBJECT, 400: OpenApiTypes.OBJECT, 403: OpenApiTypes.OBJECT, 429: OpenApiTypes.OBJECT},
                   summary="Kitchen instructions for the vendor", description="After the customer chooses, turn their plan into the requirements the kitchen must follow, using only the changes the vendor says it can make.")
    def post(self, request):
        serializer = PartnerPrepareRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        kitchen = KitchenInstructions(data["language"])
        results = [kitchen.prepare(data["profile"], item) for item in data["items"]]
        record_usage(request.partner, len(data["items"]))

        statuses = {r.status for r in results}
        return Response(
            {
                "language": data["language"],
                "needs_customer_confirmation": any(
                    i["type"] in ("remove", "substitute") for r in results for i in r.instructions
                ),
                "can_prepare_all": "cannot_make_safe" not in statuses,
                "items": [
                    {
                        "item_id": r.item_id,
                        "status": r.status,
                        "verdict": r.verdict,
                        "instructions": r.instructions,
                        "unresolved": r.unresolved,
                        "vendor_note": r.vendor_note,
                        "modified_item": r.modified_item,
                    }
                    for r in results
                ],
                "vendor_note": "\n\n".join(r.vendor_note for r in results),
            }
        )
