from rest_framework.decorators import action
from rest_framework.response import Response

from core.permissions import IsAuthenticatedViaClaims
from core.viewsets import TenantScopedModelViewSet
from products.cyed.governance.access import (
    AuditedTenantViewSet,
    IsPastoralOrLeadership,
    IsStaff,
    _email,
)
from products.cyed.wellbeing import merits
from products.cyed.wellbeing.models import (
    BehaviourIncident,
    LearnerProfile,
    WellbeingCheckIn,
    WellbeingNote,
)
from products.cyed.wellbeing.sentiment import analyse
from products.cyed.wellbeing.serializers import (
    BehaviourIncidentSerializer,
    LearnerProfileSerializer,
    WellbeingCheckInSerializer,
    WellbeingNoteSerializer,
)


class LearnerProfileViewSet(TenantScopedModelViewSet):
    """Support/disability data — staff only (teachers need it for differentiation)."""

    queryset = LearnerProfile.objects.select_related("student").all()
    serializer_class = LearnerProfileSerializer
    permission_classes = [IsStaff]

    def get_queryset(self):
        qs = super().get_queryset()
        student = self.request.query_params.get("student")
        if student:
            qs = qs.filter(student_id=student)
        return qs


class BehaviourIncidentViewSet(TenantScopedModelViewSet):
    queryset = BehaviourIncident.objects.select_related("student").all()
    serializer_class = BehaviourIncidentSerializer
    permission_classes = [IsStaff]

    def get_queryset(self):
        qs = super().get_queryset()
        params = self.request.query_params
        student = params.get("student")
        category = params.get("category")
        if student:
            qs = qs.filter(student_id=student)
        if category:
            qs = qs.filter(category=category)
        if params.get("house"):
            qs = qs.filter(house=params["house"])
        if params.get("date_from"):
            qs = qs.filter(date__gte=params["date_from"])
        if params.get("date_to"):
            qs = qs.filter(date__lte=params["date_to"])
        return qs

    def perform_create(self, serializer):
        serializer.save(
            tenant_id=self.request.tenant_id,
            reported_by=serializer.validated_data.get("reported_by") or _email(self.request),
        )

    @action(detail=False, methods=["post"], url_path="award")
    def award(self, request):
        """
        Award the same recognition to a group in one request.

        Body: ``{"students": [uuid], "category": "positive", "points": 2,
        "description": "Ran the Year 8 assembly", "house": "Kookaburra"}``

        A teacher awarding thirty merits one at a time simply will not do it,
        and a merit system nobody uses is worse than none.
        """
        student_ids = request.data.get("students") or []
        if not isinstance(student_ids, list) or not student_ids:
            return Response({"detail": "'students' must be a non-empty list of ids."}, status=400)

        category = request.data.get("category", "positive")
        if category not in {c[0] for c in BehaviourIncident.CATEGORY_CHOICES}:
            return Response({"detail": f"'{category}' is not a behaviour category."}, status=400)

        from products.cyed.sis.models import Student

        known = set(
            Student.objects.filter(
                tenant_id=request.tenant_id, id__in=student_ids
            ).values_list("id", flat=True)
        )
        missing = [s for s in student_ids if s not in {str(k) for k in known} and s not in known]
        if missing:
            return Response(
                {"detail": f"{len(missing)} student(s) are not in this school."}, status=400
            )

        created = merits.award_bulk(
            request.tenant_id,
            student_ids=list(known),
            category=category,
            points=request.data.get("points"),
            description=request.data.get("description", ""),
            reported_by=_email(request),
            house=request.data.get("house", ""),
        )
        return Response({"awarded": len(created), "category": category}, status=201)

    @action(detail=False, methods=["get"])
    def tally(self, request):
        """One student's merit position. `?student=<uuid>`."""
        from products.cyed.sis.models import Student

        student_id = request.query_params.get("student")
        if not student_id:
            return Response({"detail": "student is required."}, status=400)
        student = Student.objects.filter(tenant_id=request.tenant_id, id=student_id).first()
        if student is None:
            return Response({"detail": "No such student."}, status=404)
        return Response(merits.student_tally(
            student,
            date_from=request.query_params.get("date_from"),
            date_to=request.query_params.get("date_to"),
        ))

    @action(detail=False, methods=["get"])
    def leaderboard(self, request):
        """Students by net points, best first."""
        rows = merits.leaderboard(
            request.tenant_id,
            date_from=request.query_params.get("date_from"),
            date_to=request.query_params.get("date_to"),
            year_level=request.query_params.get("year_level"),
            limit=int(request.query_params.get("limit", 50)),
        )
        return Response({"count": len(rows), "results": rows})

    @action(detail=False, methods=["get"])
    def houses(self, request):
        """House standings — the scoreboard a merit system exists to produce."""
        rows = merits.house_standings(
            request.tenant_id,
            date_from=request.query_params.get("date_from"),
            date_to=request.query_params.get("date_to"),
        )
        return Response({"count": len(rows), "results": rows})


class WellbeingNoteViewSet(AuditedTenantViewSet):
    """
    Confidential counselling/health notes — restricted to pastoral/leadership
    (APP 6/11, health-records law) and every access audited.
    """

    queryset = WellbeingNote.objects.select_related("student").all()
    serializer_class = WellbeingNoteSerializer
    permission_classes = [IsPastoralOrLeadership]

    def get_queryset(self):
        qs = super().get_queryset()
        student = self.request.query_params.get("student")
        if student:
            qs = qs.filter(student_id=student)
        return qs


class WellbeingCheckInViewSet(TenantScopedModelViewSet):
    """
    Students (or staff) submit socio-emotional check-ins; sentiment is computed
    on save. Reading check-ins + flags is pastoral/leadership only (confidential).
    """

    queryset = WellbeingCheckIn.objects.select_related("student").all()
    serializer_class = WellbeingCheckInSerializer
    http_method_names = ["get", "post", "head", "options"]

    def get_permissions(self):
        if self.action == "create":
            return [IsAuthenticatedViaClaims()]  # student self / staff submit
        return [IsPastoralOrLeadership()]

    def get_queryset(self):
        qs = super().get_queryset()
        params = self.request.query_params
        if params.get("flagged") in ("1", "true", "True"):
            qs = qs.filter(flagged=True)
        if params.get("year_level"):
            qs = qs.filter(student__year_level=params["year_level"])
        student = params.get("student")
        if student:
            qs = qs.filter(student_id=student)
        return qs

    def perform_create(self, serializer):
        score, label, flagged = analyse(serializer.validated_data.get("response_text", ""))
        serializer.save(tenant_id=self.request.tenant_id, sentiment_score=score,
                        sentiment_label=label, flagged=flagged)

    @action(detail=False, methods=["get"], permission_classes=[IsPastoralOrLeadership])
    def cohort(self, request):
        """Aggregate sentiment across a cohort (optionally by year level)."""
        qs = self.get_queryset()
        summary = {"positive": 0, "neutral": 0, "negative": 0, "distress": 0, "flagged": 0, "total": 0}
        for c in qs:
            summary[c.sentiment_label] = summary.get(c.sentiment_label, 0) + 1
            summary["total"] += 1
            if c.flagged:
                summary["flagged"] += 1
        return Response(summary)
