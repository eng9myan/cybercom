from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from core.permissions import IsAuthenticatedViaClaims
from core.viewsets import TenantScopedModelViewSet
from products.cyed.attendance import emergency, services
from products.cyed.attendance.models import (
    AbsenceExplanation,
    AttendanceMark,
    EmergencyDrill,
    EmergencyRollEntry,
    LatePass,
    RollCall,
)
from products.cyed.attendance.printing import render_late_pass
from products.cyed.attendance.serializers import (
    AbsenceExplanationSerializer,
    AttendanceMarkSerializer,
    EmergencyDrillSerializer,
    LatePassSerializer,
    RollCallSerializer,
)
from products.cyed.governance.access import (
    CampusScopedMixin,
    IsStaff,
    _email,
    is_staff,
    scope_queryset_by_student,
    visible_student_ids,
)


class RollCallViewSet(CampusScopedMixin, TenantScopedModelViewSet):
    # A roll belongs to the campus its class section sits at.
    campus_path = "class_section__campus_id"

    queryset = RollCall.objects.select_related("class_section").prefetch_related("marks").all()
    serializer_class = RollCallSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        params = self.request.query_params
        class_section = params.get("class_section")
        date = params.get("date")
        if class_section:
            qs = qs.filter(class_section_id=class_section)
        if date:
            qs = qs.filter(date=date)
        return qs

    @action(detail=False, methods=["post"])
    def take(self, request):
        """
        Take a whole class's roll in one request.

        Body::

            {
              "class_section": "<uuid>",
              "date": "2026-08-11",
              "period_label": "P1",              # optional
              "default_status": "present",       # optional
              "marks": [                         # only the exceptions
                {"student": "<uuid>", "status": "absent"},
                {"student": "<uuid>", "status": "late", "minutes_late": 12}
              ]
            }

        Exception-based on purpose: a teacher sends the handful of students who
        are not present and everyone else on the roster is recorded with
        `default_status`. Sending no marks at all marks the class present.

        Safe to re-submit — a correction updates the existing marks, and only
        students who *newly* became absent trigger a guardian alert.
        """
        data = request.data
        if not data.get("class_section"):
            return Response({"detail": "class_section is required."}, status=status.HTTP_400_BAD_REQUEST)
        if not data.get("date"):
            return Response({"detail": "date is required."}, status=status.HTTP_400_BAD_REQUEST)

        session = getattr(request, "user_session", None) or {}
        try:
            roll_call, summary = services.take_roll(
                tenant_id=request.tenant_id,
                class_section_id=data["class_section"],
                date=data["date"],
                period_label=data.get("period_label", ""),
                marks=data.get("marks"),
                default_status=data.get("default_status", "present"),
                taken_by=data.get("taken_by") or session.get("email", "") or "",
            )
        except services.RollError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {**summary, "detail": RollCallSerializer(roll_call).data},
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["get"])
    def roster(self, request, pk=None):
        """
        Who should be on this roll, and how they are currently marked — what a
        teacher's roll screen loads before they touch anything.
        """
        roll_call = self.get_object()
        marks = {str(m.student_id): m for m in roll_call.marks.select_related("student").all()}
        rows = []
        for student_id in services.roster_student_ids(roll_call.class_section_id, request.tenant_id):
            mark = marks.get(str(student_id))
            rows.append({
                "student": str(student_id),
                "name": f"{mark.student.first_name} {mark.student.last_name}".strip() if mark else None,
                "status": mark.status if mark else None,
                "minutes_late": mark.minutes_late if mark else 0,
                "note": mark.note if mark else "",
                "marked": mark is not None,
            })
        return Response({"roll_call": str(roll_call.id), "count": len(rows), "students": rows})


class EmergencyDrillViewSet(TenantScopedModelViewSet):
    """
    Fire drills, evacuations and lockdowns.

    Staff-only and mobile-first: every response here is shaped to be read on a
    phone at an assembly point. Drills are opened through `open/` so the roll
    is snapshotted at the moment the alarm went.
    """

    queryset = EmergencyDrill.objects.select_related("campus").all()
    serializer_class = EmergencyDrillSerializer
    permission_classes = [IsStaff]
    http_method_names = ["get", "post", "head", "options"]

    def create(self, request, *args, **kwargs):
        return Response(
            {"detail": "Start a drill through /emergency-drills/open/ so the roll is captured."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    @action(detail=False, methods=["get"], url_path="on-site")
    def on_site(self, request):
        """
        Who is on site right now, with medical alerts — without starting a drill.

        Used for a real incident where nobody has time to press "start", and to
        check the roll looks right before running a scheduled drill.
        """
        return Response(emergency.roll_for(
            request.tenant_id, campus_id=request.query_params.get("campus")
        ))

    @action(detail=False, methods=["post"])
    def open(self, request):
        """Start a drill and freeze the roll. Body: {"kind": "fire_drill", "campus": uuid}."""
        kind = request.data.get("kind", "fire_drill")
        if kind not in {c[0] for c in EmergencyDrill.KIND_CHOICES}:
            return Response({"detail": f"'{kind}' is not a drill type."},
                            status=status.HTTP_400_BAD_REQUEST)

        drill = emergency.open_drill(
            request.tenant_id, kind=kind,
            campus_id=request.data.get("campus") or None,
            started_by=_email(request),
        )
        return Response(emergency.drill_status(drill), status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get"])
    def board(self, request, pk=None):
        """The live board: counts, and who is still not accounted for."""
        return Response(emergency.drill_status(self.get_object()))

    @action(detail=True, methods=["post"], url_path="account-for")
    def account_for(self, request, pk=None):
        """
        Mark people safe (or missing). Idempotent — the same student called
        twice at a noisy assembly point must not error.

        Body: ``{"students": [uuid], "state": "safe"}``
        """
        drill = self.get_object()
        if not drill.is_open():
            return Response({"detail": "This drill has already been closed."},
                            status=status.HTTP_409_CONFLICT)

        state = request.data.get("state", "safe")
        if state not in {c[0] for c in EmergencyRollEntry.STATE_CHOICES}:
            return Response({"detail": f"'{state}' is not a roll state."},
                            status=status.HTTP_400_BAD_REQUEST)

        students = request.data.get("students") or []
        if not isinstance(students, list) or not students:
            return Response({"detail": "'students' must be a non-empty list of ids."},
                            status=status.HTTP_400_BAD_REQUEST)

        updated = emergency.mark_accounted(
            drill, student_ids=students, state=state, actor=_email(request)
        )
        return Response({"updated": updated, **emergency.drill_status(drill)})

    @action(detail=True, methods=["post"])
    def close(self, request, pk=None):
        """
        End the drill. Permitted with people still unaccounted for — an
        evacuation does not wait for tidy data — but the count is frozen in.
        """
        drill = self.get_object()
        if not drill.is_open():
            return Response({"detail": "This drill has already been closed."},
                            status=status.HTTP_409_CONFLICT)
        emergency.close_drill(drill, actor=_email(request), note=request.data.get("note", ""))
        return Response(emergency.drill_status(drill))


class AbsenceExplanationViewSet(TenantScopedModelViewSet):
    """
    Families explain absences; the office accepts or declines.

    A parent may submit for their own children and read their own submissions.
    Only staff review, because an accepted explanation edits the attendance
    record the department audits.
    """

    queryset = AbsenceExplanation.objects.select_related("student").all()
    serializer_class = AbsenceExplanationSerializer
    permission_classes = [IsAuthenticatedViaClaims]
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_queryset(self):
        qs = super().get_queryset()
        qs = scope_queryset_by_student(
            self.request, self.request.tenant_id, qs, student_path="student_id"
        )
        params = self.request.query_params
        if params.get("status"):
            qs = qs.filter(status=params["status"])
        if params.get("student"):
            qs = qs.filter(student_id=params["student"])
        return qs

    def perform_create(self, serializer):
        """
        Stamp the submitter, and refuse a submission about someone else's child.

        `scope_queryset_by_student` protects reads; creation needs its own
        check because the student id arrives in the body rather than the URL.
        """
        from rest_framework.exceptions import PermissionDenied

        student = serializer.validated_data["student"]
        visible = visible_student_ids(self.request, self.request.tenant_id)
        if visible is not None and student.id not in visible:
            raise PermissionDenied("You can only explain an absence for your own child.")

        session = getattr(self.request, "user_session", None) or {}
        serializer.save(
            tenant_id=self.request.tenant_id,
            submitted_by_email=_email(self.request),
            submitted_by_name=session.get("name", "") or _email(self.request),
        )

    def partial_update(self, request, *args, **kwargs):
        """Only an unreviewed explanation is still the family's to amend."""
        if self.get_object().status != "submitted":
            return Response(
                {"detail": "This explanation has been reviewed and can no longer be changed."},
                status=status.HTTP_409_CONFLICT,
            )
        return super().partial_update(request, *args, **kwargs)

    @action(detail=False, methods=["get"])
    def pending(self, request):
        """The office's review queue, oldest absence first."""
        if not is_staff(request):
            return Response({"detail": "Staff only."}, status=status.HTTP_403_FORBIDDEN)
        rows = self.get_queryset().filter(status="submitted").order_by("start_date")
        return Response({
            "count": rows.count(),
            "results": self.get_serializer(rows, many=True).data,
        })

    @action(detail=True, methods=["post"])
    def accept(self, request, pk=None):
        """
        Accept the explanation and excuse the marks it covers.

        A forward-dated explanation legitimately excuses nothing yet — the
        absence has not happened. It is applied when the roll is taken.
        """
        if not is_staff(request):
            return Response({"detail": "Only staff may review explanations."},
                            status=status.HTTP_403_FORBIDDEN)
        explanation = self.get_object()
        try:
            updated = services.accept_explanation(
                explanation, actor=_email(request), note=request.data.get("note", "")
            )
        except services.ExplanationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_409_CONFLICT)

        return Response({
            **self.get_serializer(explanation).data,
            "marks_excused": updated,
            "planned": explanation.is_planned(),
        })

    @action(detail=True, methods=["post"])
    def decline(self, request, pk=None):
        if not is_staff(request):
            return Response({"detail": "Only staff may review explanations."},
                            status=status.HTTP_403_FORBIDDEN)
        try:
            explanation = services.decline_explanation(
                self.get_object(), actor=_email(request), note=request.data.get("note", "")
            )
        except services.ExplanationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(self.get_serializer(explanation).data)


class AttendanceMarkViewSet(TenantScopedModelViewSet):
    queryset = AttendanceMark.objects.select_related(
        "student", "roll_call", "roll_call__class_section"
    ).all()
    serializer_class = AttendanceMarkSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        # A student's attendance record is PII: parents and students see their
        # own rows only. Staff are unrestricted.
        qs = scope_queryset_by_student(self.request, self.request.tenant_id, qs, student_path="student_id")
        params = self.request.query_params
        roll_call = params.get("roll_call")
        student = params.get("student")
        if roll_call:
            qs = qs.filter(roll_call_id=roll_call)
        if student:
            qs = qs.filter(student_id=student)
        return qs


class LatePassViewSet(TenantScopedModelViewSet):
    """
    Front-office kiosk: reception issues a slip when a student signs in
    late. Staff-only (a front-desk terminal is operated by reception, not
    self-service) — a parent/student wanting their own late-arrival history
    reads it through AttendanceMark's `note`/status, not this app.
    """

    queryset = LatePass.objects.select_related("student", "class_section").all()
    serializer_class = LatePassSerializer
    permission_classes = [IsStaff]

    def get_queryset(self):
        qs = super().get_queryset()
        params = self.request.query_params
        if params.get("date"):
            qs = qs.filter(arrival_date=params["date"])
        if params.get("student"):
            qs = qs.filter(student_id=params["student"])
        return qs

    def perform_create(self, serializer):
        serializer.save(tenant_id=self.request.tenant_id, issued_by=_email(self.request))

    @action(detail=True, methods=["get"])
    def print_view(self, request, pk=None):
        """Print-ready HTML (Ctrl+P -> PDF, no PDF library needed)."""
        late_pass = self.get_object()
        if late_pass.printed_at is None:
            late_pass.printed_at = timezone.now()
            late_pass.save(update_fields=["printed_at", "updated_at"])
        return render_late_pass(late_pass)
