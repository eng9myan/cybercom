from decimal import Decimal

from django.db.models import Count, DecimalField, F, Sum
from django.db.models.functions import Coalesce
from rest_framework.decorators import action
from rest_framework.response import Response

from core.viewsets import TenantScopedModelViewSet
from products.cycom.crm.models import Activity, Lead
from products.cycom.crm.serializers import ActivitySerializer, LeadSerializer

_DEC = DecimalField(max_digits=16, decimal_places=2)
_OPEN_STAGES = ["new", "contacted", "qualified", "proposal"]


class LeadViewSet(TenantScopedModelViewSet):
    queryset = Lead.objects.all()
    serializer_class = LeadSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        stage = self.request.query_params.get("stage")
        if stage:
            qs = qs.filter(stage=stage)
        return qs

    @action(detail=False, methods=["get"])
    def pipeline(self, request):
        """Funnel data: per-stage deal count, total value, and probability-
        weighted value (value * probability%). Drives a kanban/funnel view."""
        rows = (
            super()
            .get_queryset()
            .values("stage")
            .annotate(
                count=Count("id"),
                total_value=Coalesce(Sum("estimated_value"), Decimal("0"), output_field=_DEC),
                weighted_value=Coalesce(
                    Sum(F("estimated_value") * F("probability") / Decimal("100"), output_field=_DEC),
                    Decimal("0"),
                    output_field=_DEC,
                ),
            )
        )
        by_stage = {r["stage"]: r for r in rows}
        stages = [
            {
                "stage": s,
                "label": dict(Lead.STAGE_CHOICES).get(s, s),
                "count": by_stage.get(s, {}).get("count", 0),
                "total_value": str(by_stage.get(s, {}).get("total_value", Decimal("0"))),
                "weighted_value": str(
                    (by_stage.get(s, {}).get("weighted_value") or Decimal("0")).quantize(Decimal("0.01"))
                ),
            }
            for s, _ in Lead.STAGE_CHOICES
        ]
        open_pipeline = sum(
            (Decimal(x["weighted_value"]) for x in stages if x["stage"] in _OPEN_STAGES),
            Decimal("0"),
        )
        return Response({"stages": stages, "open_weighted_pipeline": str(open_pipeline)})


class ActivityViewSet(TenantScopedModelViewSet):
    queryset = Activity.objects.all().select_related("lead")
    serializer_class = ActivitySerializer

    def get_queryset(self):
        qs = super().get_queryset()
        lead = self.request.query_params.get("lead")
        if lead:
            qs = qs.filter(lead_id=lead)
        if self.request.query_params.get("open") in ("1", "true", "yes"):
            qs = qs.filter(done=False)
        return qs
