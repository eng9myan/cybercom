from rest_framework.decorators import action
from rest_framework.response import Response

from core.viewsets import TenantScopedModelViewSet
from products.cycom.equity.models import DividendDistribution, ShareClass, ShareGrant, Shareholder
from products.cycom.equity.serializers import (
    DividendDistributionSerializer,
    ShareClassSerializer,
    ShareGrantSerializer,
    ShareholderSerializer,
)
from products.cycom.equity.services import compute_waterfall, mark_paid


class ShareClassViewSet(TenantScopedModelViewSet):
    queryset = ShareClass.objects.all()
    serializer_class = ShareClassSerializer


class ShareholderViewSet(TenantScopedModelViewSet):
    queryset = Shareholder.objects.all()
    serializer_class = ShareholderSerializer


class ShareGrantViewSet(TenantScopedModelViewSet):
    queryset = ShareGrant.objects.all()
    serializer_class = ShareGrantSerializer


class DividendDistributionViewSet(TenantScopedModelViewSet):
    queryset = DividendDistribution.objects.prefetch_related("allocations").all()
    serializer_class = DividendDistributionSerializer

    @action(detail=True, methods=["post"], url_path="compute")
    def compute(self, request, pk=None):
        # get_object() prefetches `allocations` on the queryset — that
        # cache is populated (empty) BEFORE compute_waterfall() bulk-
        # creates the real rows, so serializing the same instance
        # afterwards would return a stale empty list. Re-fetch fresh.
        compute_waterfall(self.get_object())
        dist = self.get_queryset().get(pk=pk)
        return Response(DividendDistributionSerializer(dist).data)

    @action(detail=True, methods=["post"], url_path="mark-paid")
    def mark_paid_action(self, request, pk=None):
        dist = mark_paid(self.get_object())
        return Response(DividendDistributionSerializer(dist).data)
