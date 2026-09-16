from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from core.permissions import IsAuthenticatedViaClaims
from core.viewsets import TenantScopedModelViewSet
from products.cyed.exams import services
from products.cyed.exams.models import ExamCandidate, ExamRoom, ExamRoomAllocation, ExamSitting
from products.cyed.exams.serializers import (
    ExamCandidateSerializer,
    ExamRoomAllocationSerializer,
    ExamRoomSerializer,
    ExamSittingSerializer,
)
from products.cyed.governance.access import IsStaff, scope_queryset_by_student


class ExamRoomViewSet(TenantScopedModelViewSet):
    queryset = ExamRoom.objects.select_related("campus").all()
    serializer_class = ExamRoomSerializer
    permission_classes = [IsStaff]


class ExamRoomAllocationViewSet(TenantScopedModelViewSet):
    queryset = ExamRoomAllocation.objects.select_related("room", "sitting", "invigilator").all()
    serializer_class = ExamRoomAllocationSerializer
    permission_classes = [IsStaff]

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.query_params.get("sitting"):
            qs = qs.filter(sitting_id=self.request.query_params["sitting"])
        return qs


class ExamSittingViewSet(TenantScopedModelViewSet):
    queryset = ExamSitting.objects.prefetch_related("room_allocations__room", "candidates").all()
    serializer_class = ExamSittingSerializer
    permission_classes = [IsStaff]

    def get_queryset(self):
        qs = super().get_queryset()
        params = self.request.query_params
        if params.get("date"):
            qs = qs.filter(date=params["date"])
        if params.get("year_level"):
            qs = qs.filter(year_level=params["year_level"])
        if params.get("status"):
            qs = qs.filter(status=params["status"])
        return qs

    @action(detail=True, methods=["post"], url_path="enter-cohort")
    def enter_cohort(self, request, pk=None):
        """
        Enter a group of students as candidates in one request.

        Body: ``{"students": [uuid], "class_section": "<uuid>"}`` — either an
        explicit list or everyone actively enrolled in a class section.
        """
        sitting = self.get_object()
        student_ids = request.data.get("students") or []

        if request.data.get("class_section"):
            from products.cyed.sis.models import Enrolment

            student_ids = list(
                Enrolment.objects.filter(
                    tenant_id=request.tenant_id,
                    class_section_id=request.data["class_section"],
                    status="active",
                ).values_list("student_id", flat=True)
            )
        if not student_ids:
            return Response(
                {"detail": "Give a list of students or a class section to enter."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        existing = set(
            str(s) for s in ExamCandidate.objects.filter(
                sitting=sitting
            ).values_list("student_id", flat=True)
        )
        rows = [
            ExamCandidate(tenant_id=request.tenant_id, sitting=sitting, student_id=sid)
            for sid in student_ids if str(sid) not in existing
        ]
        ExamCandidate.objects.bulk_create(rows)
        return Response({
            "sitting": str(sitting.id),
            "entered": len(rows),
            "already_entered": len(student_ids) - len(rows),
            "total_candidates": sitting.candidates.count(),
        }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="allocate-seats")
    def allocate_seats(self, request, pk=None):
        """
        Produce the seating plan.

        Deterministic and re-runnable — the same cohort and rooms always give
        the same plan, so a chart printed on Tuesday still matches the hall on
        Thursday. Refuses rather than partially seating when desks run out.
        """
        try:
            placed = services.allocate_seats(self.get_object())
        except services.ExamError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_409_CONFLICT)
        return Response({"seated": len(placed), "chart": services.seating_chart(self.get_object())})

    @action(detail=True, methods=["get"], url_path="seating-chart")
    def seating_chart(self, request, pk=None):
        """The plan an invigilator carries into the room."""
        return Response(services.seating_chart(self.get_object()))

    @action(detail=True, methods=["post"], url_path="issue-tickets")
    def issue_tickets(self, request, pk=None):
        try:
            issued = services.issue_tickets(self.get_object())
        except services.ExamError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_409_CONFLICT)
        return Response({"issued": len(issued)})

    @action(detail=True, methods=["get"])
    def register(self, request, pk=None):
        """The attendance register signed in the hall."""
        return Response(services.attendance_register(self.get_object()))


class ExamCandidateViewSet(TenantScopedModelViewSet):
    """
    Candidates, and the hall ticket a student collects.

    Students and parents may read their own ticket — that is the point of a
    ticket — but everything else here is staff-only.
    """

    queryset = ExamCandidate.objects.select_related("student", "sitting", "room").all()
    serializer_class = ExamCandidateSerializer

    def get_permissions(self):
        if self.action in ("ticket", "list", "retrieve"):
            return [IsAuthenticatedViaClaims()]
        return [IsStaff()]

    def get_queryset(self):
        qs = super().get_queryset()
        qs = scope_queryset_by_student(
            self.request, self.request.tenant_id, qs, student_path="student_id"
        )
        params = self.request.query_params
        if params.get("sitting"):
            qs = qs.filter(sitting_id=params["sitting"])
        if params.get("student"):
            qs = qs.filter(student_id=params["student"])
        return qs

    @action(detail=True, methods=["get"])
    def ticket(self, request, pk=None):
        candidate = self.get_object()
        if not candidate.ticket_number:
            return Response(
                {"detail": "No hall ticket has been issued for this exam yet."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(services.hall_ticket(candidate))

    @action(detail=True, methods=["post"], url_path="mark-attendance", permission_classes=[IsStaff])
    def mark_attendance(self, request, pk=None):
        candidate = self.get_object()
        value = request.data.get("attendance")
        if value not in {c[0] for c in ExamCandidate.ATTENDANCE_CHOICES}:
            return Response({"detail": f"'{value}' is not an attendance value."}, status=400)
        candidate.attendance = value
        candidate.save(update_fields=["attendance", "updated_at"])
        return Response(self.get_serializer(candidate).data)
