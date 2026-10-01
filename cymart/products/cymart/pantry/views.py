from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import (
    ExplodeRecipesSerializer,
    MatchedIngredientSerializer,
    PantryItemSerializer,
    RecordPurchaseSerializer,
    UnmatchedIngredientSerializer,
)
from .services import GroceryListBuilder, ReplenishEngine


def _customer_id(request):
    """The caller's id from the verified JWT — never a client param."""
    return request.user_session["user_id"]


class PurchaseView(APIView):
    """Manual 'I bought this elsewhere' log. Checkout logs automatically
    (see cart.services.CartService) — this covers what CyMart didn't
    deliver, so the replenish prediction still learns the right rhythm."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = RecordPurchaseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item = ReplenishEngine().record_purchase(
            customer_id=_customer_id(request),
            source="manual",
            **serializer.validated_data,
        )
        return Response(
            {
                "product_id": item.product_id,
                "typical_interval_days": item.typical_interval_days,
                "predicted_runout_date": item.predicted_runout_date,
            },
            status=201,
        )


class ReplenishView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        basket = ReplenishEngine().build_refill_basket(_customer_id(request))
        return Response(PantryItemSerializer(basket, many=True).data)


class ExplodeRecipesView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ExplodeRecipesSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = GroceryListBuilder().from_recipes(
            serializer.validated_data["codes"],
            serializer.validated_data.get("servings_map"),
        )
        return Response(
            {
                "matched": MatchedIngredientSerializer(result["matched"], many=True).data,
                "unmatched": UnmatchedIngredientSerializer(result["unmatched"], many=True).data,
            }
        )


class PlanBasketView(APIView):
    """This week's grocery basket that fits the caller's active diet
    plan — the grocery-side equivalent of dietshield's meal filtering."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        from products.cymart.dietshield.services import ProfileService

        profile = ProfileService().get(_customer_id(request))
        if profile is None:
            return Response({"detail": "No diet profile yet."}, status=404)
        days = int(request.query_params.get("days", 7))
        return Response(GroceryListBuilder().from_plan(profile, days=days))
