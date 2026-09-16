from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from core.viewsets import TenantScopedModelViewSet
from products.cyed.governance.access import IsStaff
from products.cyed.substitution import relief, services
from products.cyed.substitution.models import (
    ReliefAvailability,
    ReliefBooking,
    ReliefTeacher,
    SubstitutionAssignment,
    SubstitutionPlan,
)
from products.cyed.substitution.serializers import (
    ReliefAvailabilitySerializer,
    ReliefBookingSerializer,
    ReliefTeacherSerializer,
    SubstitutionAssignmentSerializer,
    SubstitutionPlanSerializer,
)


class SubstitutionPlanViewSet(TenantScopedModelViewSet):
    queryset = SubstitutionPlan.objects.prefetch_related("assignments").all()
    serializer_class = SubstitutionPlanSerializer
    permission_classes = [IsStaff]

    def _actor(self, request):
        return (getattr(request, "user_session", {}) or {}).get("email", "")

    @action(detail=True, methods=["get"])
    def coverage(self, request, pk=None):
        """
        Where the plan stands, including relief booked against its gaps.

        Only *accepted* bookings count toward cover. An unanswered offer shown
        as covered is how a class ends up unattended with a board saying
        otherwise.
        """
        plan = self.get_object()
        booked = relief.cover_for_plan(plan)
        return Response({
            "plan": str(plan.id),
            "covered_internally": plan.covered_count,
            "gaps": plan.gap_count,
            "relief_booked": len(booked),
            "still_uncovered": max(0, plan.gap_count - len(booked)),
            "relief": booked,
        })

    @action(detail=False, methods=["post"])
    def generate(self, request):
        """
        Propose cover for an absent teacher's classes.

        Body: ``{"absent_staff": "<uuid>", "day_of_week": "mon", "date": "…"}``

        `absent_staff` is the real identifier. `absent_teacher` (a name) is
        still accepted for legacy callers and resolved to a Staff record where
        the match is unambiguous — but a name that matches two people is left
        unresolved rather than guessed, because guessing is the bug this engine
        was rewritten to remove.

        Passing `date` is worth doing: it lets the engine exclude colleagues
        who are themselves away that day.
        """
        from products.cyed.hr.models import Staff

        day = (request.data.get("day_of_week") or "").strip()
        absent_name = (request.data.get("absent_teacher") or "").strip()
        absent_staff_id = request.data.get("absent_staff")

        if not day or not (absent_name or absent_staff_id):
            return Response(
                {"detail": "day_of_week and one of absent_staff or absent_teacher are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        staff = None
        if absent_staff_id:
            staff = Staff.objects.filter(
                tenant_id=request.tenant_id, id=absent_staff_id
            ).first()
            if staff is None:
                return Response({"detail": "No such staff member in this school."},
                                status=status.HTTP_400_BAD_REQUEST)

        plan = services.build_plan(
            request.tenant_id,
            absent_teacher=absent_name,
            absent_staff=staff,
            day_of_week=day,
            date=request.data.get("date") or None,
            generated_by=self._actor(request),
        )
        return Response(self.get_serializer(plan).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["get"], url_path="cover-pool")
    def cover_pool(self, request):
        """
        Who could cover a class right now, and why anyone was ruled out.

        Useful before generating: an empty pool on a Monday morning is a
        staffing problem, not a scheduling one.
        """
        eligible, excluded = services.cover_pool(
            request.tenant_id, date=request.query_params.get("date") or None
        )
        return Response({
            "eligible": [
                {"staff": str(s.id), "name": f"{s.first_name} {s.last_name}".strip()}
                for s in eligible
            ],
            "excluded": [
                {"staff": str(s.id), "name": f"{s.first_name} {s.last_name}".strip(), "reason": r}
                for s, r in excluded
            ],
        })


class ReliefTeacherViewSet(TenantScopedModelViewSet):
    """The school's CRT register. Staff-only — it carries clearance data."""

    queryset = ReliefTeacher.objects.select_related("campus").all()
    serializer_class = ReliefTeacherSerializer
    permission_classes = [IsStaff]

    def get_queryset(self):
        qs = super().get_queryset()
        params = self.request.query_params
        if params.get("status"):
            qs = qs.filter(status=params["status"])
        if params.get("agency"):
            qs = qs.filter(agency__icontains=params["agency"])
        return qs

    def perform_create(self, serializer):
        self._save_with_verification(serializer)

    def perform_update(self, serializer):
        self._save_with_verification(serializer)

    def _save_with_verification(self, serializer):
        """Stamp who sighted the clearances — same rule as employed staff."""
        extra = {"tenant_id": self.request.tenant_id}
        if serializer.validated_data.get("verified_on"):
            extra["verified_by"] = self._actor(self.request)
        serializer.save(**extra)

    @action(detail=False, methods=["get"])
    def available(self, request):
        """
        Who can work a given day. `?date=2026-08-14&subject=Mathematics`

        Availability must have been stated — ringing people on the off-chance
        at 7am is what this replaces.
        """
        day = request.query_params.get("date")
        if not day:
            return Response({"detail": "date is required."}, status=status.HTTP_400_BAD_REQUEST)
        rows = relief.available_on(
            request.tenant_id, day,
            subject=request.query_params.get("subject", ""),
            campus_id=request.query_params.get("campus"),
        )
        return Response({"count": len(rows), "date": day, "results": rows})

    @action(detail=False, methods=["get"], url_path="clearance-issues")
    def clearance_issues(self, request):
        """
        Active CRTs who cannot be booked, and why — the chase list, and the
        answer to "why did the availability search come back empty?".
        """
        rows = relief.unclearable(request.tenant_id)
        return Response({"count": len(rows), "results": rows})

    @action(detail=True, methods=["post"])
    def offer(self, request, pk=None):
        """
        Offer a day's work. Body: ``{"date": "...", "plan": uuid, "periods":
        "P1, P2", "is_full_day": true}``
        """
        teacher = self.get_object()
        day = request.data.get("date")
        if not day:
            return Response({"detail": "date is required."}, status=status.HTTP_400_BAD_REQUEST)

        plan = None
        if request.data.get("plan"):
            plan = SubstitutionPlan.objects.filter(
                tenant_id=request.tenant_id, id=request.data["plan"]
            ).first()

        try:
            booking = relief.offer(
                teacher, day=day, plan=plan,
                periods=request.data.get("periods", ""),
                is_full_day=bool(request.data.get("is_full_day", True)),
                offered_by=self._actor(request),
                cost_centre=request.data.get("cost_centre", ""),
            )
        except relief.ReliefError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_409_CONFLICT)
        return Response(ReliefBookingSerializer(booking).data, status=status.HTTP_201_CREATED)

    def _actor(self, request):
        return (getattr(request, "user_session", {}) or {}).get("email", "")


class ReliefAvailabilityViewSet(TenantScopedModelViewSet):
    queryset = ReliefAvailability.objects.select_related("relief_teacher").all()
    serializer_class = ReliefAvailabilitySerializer
    permission_classes = [IsStaff]

    def get_queryset(self):
        qs = super().get_queryset()
        params = self.request.query_params
        if params.get("relief_teacher"):
            qs = qs.filter(relief_teacher_id=params["relief_teacher"])
        if params.get("date"):
            qs = qs.filter(date=params["date"])
        return qs


class ReliefBookingViewSet(TenantScopedModelViewSet):
    """
    Offers of work and their outcomes.

    Read-only except for the response actions: bookings are created through
    `relief-teachers/{id}/offer/` so the clearance and double-booking checks
    cannot be bypassed.
    """

    queryset = ReliefBooking.objects.select_related("relief_teacher", "plan").all()
    serializer_class = ReliefBookingSerializer
    permission_classes = [IsStaff]
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self):
        qs = super().get_queryset()
        params = self.request.query_params
        if params.get("date"):
            qs = qs.filter(date=params["date"])
        if params.get("status"):
            qs = qs.filter(status=params["status"])
        if params.get("plan"):
            qs = qs.filter(plan_id=params["plan"])
        return qs

    def create(self, request, *args, **kwargs):
        return Response(
            {"detail": "Offer work through /relief-teachers/{id}/offer/."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    @action(detail=True, methods=["post"])
    def accept(self, request, pk=None):
        return self._respond(request, accepted=True)

    @action(detail=True, methods=["post"])
    def decline(self, request, pk=None):
        return self._respond(request, accepted=False)

    def _respond(self, request, *, accepted):
        try:
            booking = relief.respond(
                self.get_object(), accepted=accepted, note=request.data.get("note", "")
            )
        except relief.ReliefError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_409_CONFLICT)
        return Response(self.get_serializer(booking).data)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        try:
            booking = relief.cancel(self.get_object(), reason=request.data.get("reason", ""))
        except relief.ReliefError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_409_CONFLICT)
        return Response(self.get_serializer(booking).data)

    @action(detail=False, methods=["get"], url_path="cost-report")
    def cost_report(self, request):
        """What relief has cost — the figure asked for at every finance meeting."""
        return Response(relief.cost_report(
            request.tenant_id,
            date_from=request.query_params.get("date_from"),
            date_to=request.query_params.get("date_to"),
        ))


class SubstitutionAssignmentViewSet(TenantScopedModelViewSet):
    queryset = SubstitutionAssignment.objects.select_related("plan").all()
    serializer_class = SubstitutionAssignmentSerializer
    permission_classes = [IsStaff]

    def get_queryset(self):
        qs = super().get_queryset()
        plan = self.request.query_params.get("plan")
        if plan:
            qs = qs.filter(plan_id=plan)
        return qs
