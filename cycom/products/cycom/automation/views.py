from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import IsAuthenticatedViaClaims
from core.viewsets import TenantScopedModelViewSet
from products.cycom.automation.engine import rule_matches
from products.cycom.automation.models import AutomationRule, AutomationRun
from products.cycom.automation.registry import catalog, source_config
from products.cycom.automation.serializers import AutomationRuleSerializer, AutomationRunSerializer


class AutomationCatalogView(APIView):
    """Everything the rule builder needs to render: sources, their readable
    and writable fields, operators, action types, trigger events."""

    permission_classes = [IsAuthenticatedViaClaims]

    def get(self, request):
        return Response(catalog())


class AutomationRuleViewSet(TenantScopedModelViewSet):
    queryset = AutomationRule.objects.prefetch_related("runs").all()
    serializer_class = AutomationRuleSerializer
    filterset_fields = ["trigger_source", "is_active"]

    @action(detail=True, methods=["post"], url_path="dry-run")
    def dry_run(self, request, pk=None):
        """Evaluate this rule's conditions against an existing record
        WITHOUT running any action -- lets someone check a rule before
        arming it, instead of finding out by mutating live data."""
        rule = self.get_object()
        record_id = request.data.get("record_id")
        if not record_id:
            return Response({"detail": "record_id is required."}, status=400)

        cfg = source_config(rule.trigger_source)
        if not cfg:
            return Response({"detail": "Rule has an unknown trigger source."}, status=400)

        instance = cfg["model"].objects.filter(
            pk=record_id, tenant_id=request.tenant_id,
        ).first()
        if instance is None:
            return Response({"detail": "Record not found."}, status=404)

        matched = rule_matches(rule, instance, previous=None)
        return Response({
            "matched": matched,
            "record_id": str(instance.pk),
            "would_run": [a.get("type") for a in (rule.actions or [])] if matched else [],
            "note": "Conditions using 'changed to' can only be evaluated on a real update, not a dry run.",
        })


class AutomationRunViewSet(TenantScopedModelViewSet):
    queryset = AutomationRun.objects.select_related("rule").all()
    serializer_class = AutomationRunSerializer
    filterset_fields = ["rule", "status"]
    http_method_names = ["get", "head", "options"]
