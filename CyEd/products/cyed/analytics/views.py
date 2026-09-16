from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from products.cyed.analytics.services import compute_at_risk
from products.cyed.governance.access import IsFinanceOrLeadership as _IsFinanceOrLeadership
from products.cyed.governance.access import IsPastoralOrLeadership


class AtRiskView(APIView):
    """
    GET /api/v1/analytics/at-risk/?band=high
    Predictive student-success signal from attendance + grades + behaviour.
    Sensitive welfare inference — restricted to pastoral/leadership.
    """

    permission_classes = [IsPastoralOrLeadership]

    def get(self, request):
        tenant_id = getattr(request, "tenant_id", None)
        if tenant_id is None:
            return Response({"detail": "A tenant context is required."}, status=status.HTTP_400_BAD_REQUEST)
        rows = compute_at_risk(tenant_id)
        band = request.query_params.get("band")
        if band:
            rows = [r for r in rows if r["risk_band"] == band]
        summary = {
            "high": sum(1 for r in rows if r["risk_band"] == "high"),
            "medium": sum(1 for r in rows if r["risk_band"] == "medium"),
            "low": sum(1 for r in rows if r["risk_band"] == "low"),
        }
        return Response({"summary": summary, "students": rows})


class FeeRiskView(APIView):
    """
    GET /api/v1/analytics/fee-risk/
    Predictive fee-collection risk per student + cash-flow forecast.
    Finance/leadership only.
    """

    permission_classes = [_IsFinanceOrLeadership]

    def get(self, request):
        tenant_id = getattr(request, "tenant_id", None)
        if tenant_id is None:
            return Response({"detail": "A tenant context is required."}, status=status.HTTP_400_BAD_REQUEST)
        from products.cyed.analytics.fee_analytics import compute_fee_risk
        return Response(compute_fee_risk(tenant_id))


class DashboardView(APIView):
    """
    GET /api/v1/analytics/dashboard/?weeks=20&campus=<uuid>

    School-wide analytics for executive leadership: attendance trend, weakest
    year levels, students below the chronic-absence line, achievement spread
    and behaviour.

    Leadership-only. These are whole-school aggregates, and the chronic-absence
    list names individual children — a teacher who needs that for their own
    class has it on the at-risk view, scoped to the students they teach.
    """

    permission_classes = [IsPastoralOrLeadership]

    def get(self, request):
        from products.cyed.analytics import dashboards

        try:
            weeks = int(request.query_params.get("weeks", 20))
        except ValueError:
            return Response({"detail": "weeks must be a whole number."},
                            status=status.HTTP_400_BAD_REQUEST)
        # A ceiling because the window drives the scan: an unbounded "weeks"
        # would let one request read every mark the school has ever recorded.
        weeks = max(1, min(weeks, 60))

        return Response(dashboards.overview(
            getattr(request, "tenant_id", None),
            weeks=weeks,
            campus_id=request.query_params.get("campus"),
        ))


class CampusComparisonView(APIView):
    """
    GET /api/v1/analytics/campus-comparison/?weeks=20

    Every campus side by side — the view that only matters to a group.
    """

    permission_classes = [IsPastoralOrLeadership]

    def get(self, request):
        from products.cyed.analytics import dashboards

        try:
            weeks = max(1, min(int(request.query_params.get("weeks", 20)), 60))
        except ValueError:
            return Response({"detail": "weeks must be a whole number."},
                            status=status.HTTP_400_BAD_REQUEST)

        rows = dashboards.campus_comparison(getattr(request, "tenant_id", None), weeks=weeks)
        return Response({"weeks": weeks, "count": len(rows), "results": rows})
