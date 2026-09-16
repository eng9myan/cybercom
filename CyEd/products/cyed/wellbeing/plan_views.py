"""
Support plan (IEP) endpoints.

Separate module from `views.py` so the plan lifecycle — activation,
supersession, reviews, the NCCD evidence report — sits together rather than
being scattered through the wider wellbeing surface.
"""

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from core.viewsets import TenantScopedModelViewSet
from products.cyed.governance.access import (
    AuditedTenantViewSet,
    IsPastoralOrLeadership,
    IsStaff,
    _email,
)
from products.cyed.wellbeing import support_plans
from products.cyed.wellbeing.models import (
    SupportAdjustment,
    SupportGoal,
    SupportPlan,
)
from products.cyed.wellbeing.serializers import (
    SupportAdjustmentSerializer,
    SupportGoalSerializer,
    SupportPlanReviewSerializer,
    SupportPlanSerializer,
)


class SupportPlanViewSet(AuditedTenantViewSet):
    """
    Individual education plans.

    Pastoral/leadership only and every access audited: a plan carries
    disability information, family consultation notes and a student's own
    words. Teachers who need to *act* on an adjustment get it through the
    student's profile rather than the whole plan.
    """

    queryset = SupportPlan.objects.select_related("student", "coordinator").prefetch_related(
        "adjustments", "goals", "reviews"
    ).all()
    serializer_class = SupportPlanSerializer
    permission_classes = [IsPastoralOrLeadership]

    def get_queryset(self):
        qs = super().get_queryset()
        params = self.request.query_params
        if params.get("student"):
            qs = qs.filter(student_id=params["student"])
        if params.get("status"):
            qs = qs.filter(status=params["status"])
        if params.get("plan_type"):
            qs = qs.filter(plan_type=params["plan_type"])
        return qs

    @action(detail=True, methods=["post"])
    def activate(self, request, pk=None):
        """
        Put the plan in force, superseding any earlier plan of the same type.

        Refused without adjustments — a plan that changes nothing is not
        evidence of support, and reporting it to NCCD would be a claim the
        school cannot stand behind.
        """
        try:
            plan = support_plans.activate(self.get_object(), actor=_email(request))
        except support_plans.SupportPlanError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_409_CONFLICT)
        return Response(self.get_serializer(plan).data)

    @action(detail=True, methods=["post"])
    def close(self, request, pk=None):
        try:
            plan = support_plans.close(
                self.get_object(), reason=request.data.get("reason", ""), actor=_email(request)
            )
        except support_plans.SupportPlanError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_409_CONFLICT)
        return Response(self.get_serializer(plan).data)

    @action(detail=True, methods=["post"], url_path="record-review")
    def record_review(self, request, pk=None):
        """
        Record a review meeting and roll the next review date forward.

        Body: ``{"held_on": "...", "participants": "...", "family_present": true,
        "outcome": "...", "next_review_due": "..."}``
        """
        try:
            review = support_plans.record_review(
                self.get_object(),
                held_on=request.data.get("held_on"),
                participants=request.data.get("participants", ""),
                family_present=bool(request.data.get("family_present")),
                student_present=bool(request.data.get("student_present")),
                discussion=request.data.get("discussion", ""),
                outcome=request.data.get("outcome", ""),
                next_review_due=request.data.get("next_review_due") or None,
                recorded_by=_email(request),
            )
        except support_plans.SupportPlanError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(SupportPlanReviewSerializer(review).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["get"], url_path="needing-review")
    def needing_review(self, request):
        """Overdue or soon-due plans — the coordinator's worklist."""
        rows = support_plans.plans_needing_review(request.tenant_id)
        return Response({"count": len(rows), "results": rows})

    @action(detail=False, methods=["get"], url_path="nccd-evidence")
    def nccd_evidence(self, request):
        """
        The NCCD return, derived from the plans actually in force.

        Rows with thin evidence are flagged rather than dropped — a school
        needs to see which of its claims would not survive an audit before an
        auditor does.
        """
        year = request.query_params.get("year")
        return Response(support_plans.nccd_evidence(
            request.tenant_id, year=int(year) if year else None
        ))


class SupportAdjustmentViewSet(TenantScopedModelViewSet):
    """
    Adjustments on a plan.

    Readable by any staff member: a teacher — including a relief teacher —
    has to know what to do differently, and a plan they cannot open is one
    that does not get followed. The surrounding plan, with its diagnosis and
    family notes, stays pastoral-only.
    """

    queryset = SupportAdjustment.objects.select_related("plan", "plan__student").all()
    serializer_class = SupportAdjustmentSerializer

    def get_permissions(self):
        if self.action in ("list", "retrieve", "for_student"):
            return [IsStaff()]
        return [IsPastoralOrLeadership()]

    def get_queryset(self):
        qs = super().get_queryset()
        params = self.request.query_params
        if params.get("plan"):
            qs = qs.filter(plan_id=params["plan"])
        if params.get("student"):
            qs = qs.filter(plan__student_id=params["student"])
        return qs

    @action(detail=False, methods=["get"], url_path="for-student")
    def for_student(self, request):
        """
        What a teacher needs to do differently for one student, today.

        Active adjustments from active plans only — a superseded plan's
        adjustments are history, and following them would be wrong.
        """
        student_id = request.query_params.get("student")
        if not student_id:
            return Response({"detail": "student is required."},
                            status=status.HTTP_400_BAD_REQUEST)

        rows = self.get_queryset().filter(
            plan__student_id=student_id, plan__status="active", is_active=True
        )
        return Response({
            "student": student_id,
            "count": rows.count(),
            "results": self.get_serializer(rows, many=True).data,
        })


class SupportGoalViewSet(TenantScopedModelViewSet):
    queryset = SupportGoal.objects.select_related("plan").all()
    serializer_class = SupportGoalSerializer
    permission_classes = [IsPastoralOrLeadership]

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.query_params.get("plan"):
            qs = qs.filter(plan_id=self.request.query_params["plan"])
        return qs

    @action(detail=True, methods=["post"], url_path="record-progress")
    def record_progress(self, request, pk=None):
        """Update how a goal is tracking, and stamp when that was assessed."""
        from django.utils import timezone

        goal = self.get_object()
        progress = request.data.get("progress")
        if progress not in {c[0] for c in SupportGoal.PROGRESS_CHOICES}:
            return Response({"detail": f"'{progress}' is not a progress value."},
                            status=status.HTTP_400_BAD_REQUEST)
        goal.progress = progress
        goal.progress_note = request.data.get("note", "")
        goal.progress_updated_on = timezone.localdate()
        goal.save(update_fields=[
            "progress", "progress_note", "progress_updated_on", "updated_at",
        ])
        return Response(self.get_serializer(goal).data)
