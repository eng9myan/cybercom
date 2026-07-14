from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import CommissionCalculation, CommissionPolicy
from .serializers import CommissionCalculationSerializer, CommissionPolicySerializer


class CommissionPolicyViewSet(viewsets.ModelViewSet):
    queryset = CommissionPolicy.objects.all().order_by("-effective_from")
    serializer_class = CommissionPolicySerializer
    permission_classes = [IsAuthenticated]


class CommissionCalculationViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only — calculations are an immutable ledger, created only by
    CommissionEngine, never through the API directly."""

    serializer_class = CommissionCalculationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = CommissionCalculation.objects.all().order_by("-created_at")
        tenant_id = self.request.query_params.get("tenant_id")
        reference_id = self.request.query_params.get("reference_id")
        if tenant_id:
            qs = qs.filter(tenant_id=tenant_id)
        if reference_id:
            qs = qs.filter(reference_id=reference_id)
        return qs
