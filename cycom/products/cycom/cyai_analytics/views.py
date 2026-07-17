from datetime import timedelta

from django.db.models import Avg, Count, Sum
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import IsAuthenticatedViaClaims
from platform.cyai.models import InferenceLog
from products.cycom.cyai_memory.models import MemoryQueryLog
from products.cycom.cyai_moduledev.models import ModuleDevRequest
from products.cycom.cyai_reports.models import ReportBuilderSession, ReportDefinition


class CyaiUsageAnalyticsView(APIView):
    """
    Real aggregation over every audit trail the CyAI platform already
    writes — InferenceLog (every LLM call), MemoryQueryLog (every local
    Q&A), ModuleDevRequest (every module-dev workflow action), report
    sessions/definitions. No separate logging system; this just summarizes
    what's already recorded.
    """

    permission_classes = [IsAuthenticatedViaClaims]

    def get(self, request):
        days = int(request.query_params.get("days", 30))
        since = timezone.now() - timedelta(days=days)
        tenant_id = getattr(request, "tenant_id", None)

        inference_qs = InferenceLog.objects.filter(created_at__gte=since)
        if tenant_id:
            inference_qs = inference_qs.filter(tenant_id=tenant_id)
        inference_by_verdict = dict(
            inference_qs.values_list("safety_verdict").annotate(c=Count("id")).order_by()
        )
        inference_totals = inference_qs.aggregate(
            total_prompt_tokens=Sum("tokens_prompt"),
            total_completion_tokens=Sum("tokens_completion"),
            avg_latency_ms=Avg("latency_ms"),
        )

        memory_qs = MemoryQueryLog.objects.filter(created_at__gte=since)
        if tenant_id:
            memory_qs = memory_qs.filter(tenant_id=tenant_id)
        memory_by_plan = dict(
            memory_qs.exclude(matched_plan_code="")
            .values_list("matched_plan_code")
            .annotate(c=Count("id"))
            .order_by()
        )
        memory_unmatched = memory_qs.filter(matched_plan_code="").count()

        moduledev_qs = ModuleDevRequest.objects.filter(created_at__gte=since)
        if tenant_id:
            moduledev_qs = moduledev_qs.filter(tenant_id=tenant_id)
        moduledev_by_status = dict(
            moduledev_qs.values_list("status").annotate(c=Count("id")).order_by()
        )

        sessions_qs = ReportBuilderSession.objects.filter(created_at__gte=since)
        reports_qs = ReportDefinition.objects.filter(created_at__gte=since)
        if tenant_id:
            sessions_qs = sessions_qs.filter(tenant_id=tenant_id)
            reports_qs = reports_qs.filter(tenant_id=tenant_id)

        return Response(
            {
                "period_days": days,
                "llm_calls": {
                    "total": inference_qs.count(),
                    "by_safety_verdict": inference_by_verdict,
                    "total_prompt_tokens": inference_totals["total_prompt_tokens"] or 0,
                    "total_completion_tokens": inference_totals["total_completion_tokens"] or 0,
                    "avg_latency_ms": round(inference_totals["avg_latency_ms"] or 0, 1),
                },
                "local_memory_agent": {
                    "total_questions": memory_qs.count(),
                    "matched_by_plan": memory_by_plan,
                    "unmatched": memory_unmatched,
                },
                "module_developer": {
                    "total_requests": moduledev_qs.count(),
                    "by_status": moduledev_by_status,
                },
                "report_builder": {
                    "sessions_started": sessions_qs.count(),
                    "sessions_confirmed": sessions_qs.filter(status="confirmed").count(),
                    "reports_saved": reports_qs.count(),
                },
            }
        )
