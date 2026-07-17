from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from core.permissions import IsAuthenticatedViaClaims
from core.viewsets import TenantScopedModelViewSet
from products.cycom.cyai_memory.models import MemoryQueryLog, QueryPlan
from products.cycom.cyai_memory.serializers import (
    AskQuestionSerializer,
    MemoryQueryLogSerializer,
    QueryPlanSerializer,
)
from products.cycom.cyai_memory.services import LocalMemoryAgent


class QueryPlanViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only registry — plans are code-defined in plans.py, this is the
    discoverable/auditable catalog of what's actually runnable. Not
    tenant-scoped: the same plan catalog applies to every tenant."""

    queryset = QueryPlan.objects.all()
    serializer_class = QueryPlanSerializer
    permission_classes = [IsAuthenticatedViaClaims]

    @action(detail=False, methods=["post"], url_path="ask")
    def ask(self, request):
        ser = AskQuestionSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        claims = getattr(request, "auth_claims", {}) or {}
        result = LocalMemoryAgent.answer(
            tenant_id=request.tenant_id,
            question=ser.validated_data["question"],
            asked_by=claims.get("email", ""),
        )
        return Response(result)


class MemoryQueryLogViewSet(TenantScopedModelViewSet):
    queryset = MemoryQueryLog.objects.all()
    serializer_class = MemoryQueryLogSerializer
    http_method_names = ["get", "head", "options"]
