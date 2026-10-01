from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Merchant
from .serializers import MerchantSerializer, MerchantWithProductsSerializer
from .services import CatalogSearch


class MerchantListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        kind = request.query_params.get("kind")
        qs = Merchant.objects.filter(is_active=True)
        if kind:
            qs = qs.filter(kind=kind)
        return Response(MerchantSerializer(qs, many=True).data)


class MerchantDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, merchant_id):
        try:
            merchant = Merchant.objects.get(id=merchant_id, is_active=True)
        except Merchant.DoesNotExist:
            return Response({"detail": "Merchant not found."}, status=404)
        return Response(MerchantWithProductsSerializer(merchant).data)


class CatalogSearchView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        query = request.query_params.get("q", "")
        kind = request.query_params.get("kind")
        results = CatalogSearch().search(query, kind=kind, limit=20)
        return Response(results)
