from decimal import Decimal

from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import IsAuthenticatedViaClaims
from core.viewsets import TenantScopedModelViewSet
from products.cycom.esg.models import EmissionEntry, EmissionFactor
from products.cycom.esg.serializers import EmissionEntrySerializer, EmissionFactorSerializer


class EmissionFactorViewSet(TenantScopedModelViewSet):
    queryset = EmissionFactor.objects.all()
    serializer_class = EmissionFactorSerializer


class EmissionEntryViewSet(TenantScopedModelViewSet):
    queryset = EmissionEntry.objects.select_related("factor").all()
    serializer_class = EmissionEntrySerializer

    def get_queryset(self):
        qs = super().get_queryset()
        after = self.request.query_params.get("after")
        before = self.request.query_params.get("before")
        scope = self.request.query_params.get("scope")
        if after:
            qs = qs.filter(activity_date__gte=after)
        if before:
            qs = qs.filter(activity_date__lte=before)
        if scope:
            qs = qs.filter(scope=scope)
        return qs


class EmissionReportView(APIView):
    """
    GET /api/v1/esg/report/?after=YYYY-MM-DD&before=YYYY-MM-DD
    Aggregates logged entries by scope and by activity — an internal
    summary export, not a pre-formatted regulatory filing template.
    """

    permission_classes = [IsAuthenticatedViaClaims]

    def get(self, request):
        tenant_id = getattr(request, "tenant_id", None)
        qs = EmissionEntry.objects.select_related("factor").all()
        if tenant_id:
            qs = qs.filter(tenant_id=tenant_id)
        after = request.query_params.get("after")
        before = request.query_params.get("before")
        if after:
            qs = qs.filter(activity_date__gte=after)
        if before:
            qs = qs.filter(activity_date__lte=before)

        by_scope = {}
        by_activity = {}
        total = Decimal("0")
        for entry in qs:
            by_scope[entry.scope] = by_scope.get(entry.scope, Decimal("0")) + entry.co2e_kg
            by_activity[entry.factor.activity_name] = (
                by_activity.get(entry.factor.activity_name, Decimal("0")) + entry.co2e_kg
            )
            total += entry.co2e_kg

        return Response(
            {
                "total_co2e_kg": str(total),
                "by_scope": {k: str(v) for k, v in by_scope.items()},
                "by_activity": {k: str(v) for k, v in by_activity.items()},
                "entry_count": qs.count(),
            }
        )
