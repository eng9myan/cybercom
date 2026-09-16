"""
Interview booking endpoints.

Kept apart from `views.py`, which owns meeting transcripts and summaries — a
different feature that happens to share the word "meeting".
"""

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from core.permissions import IsAuthenticatedViaClaims
from core.viewsets import TenantScopedModelViewSet
from products.cyed.governance.access import IsStaff, _email, is_staff, visible_student_ids
from products.cyed.meetings import interviews
from products.cyed.meetings.interview_serializers import (
    InterviewBookingSerializer,
    InterviewRoundSerializer,
    InterviewSlotSerializer,
)
from products.cyed.meetings.models import InterviewBooking, InterviewRound, InterviewSlot


class InterviewRoundViewSet(TenantScopedModelViewSet):
    """
    Interview periods. Families read published rounds; staff create them.
    """

    queryset = InterviewRound.objects.select_related("academic_year", "campus").all()
    serializer_class = InterviewRoundSerializer

    def get_permissions(self):
        if self.action in ("list", "retrieve", "slots", "my_schedule"):
            return [IsAuthenticatedViaClaims()]
        return [IsStaff()]

    def get_queryset(self):
        qs = super().get_queryset()
        # An unpublished round is a draft the office is still building; a
        # family seeing it would book against slots that may be deleted.
        if not is_staff(self.request):
            qs = qs.filter(is_published=True)
        return qs

    @action(detail=True, methods=["post"], url_path="generate-slots")
    def generate_slots(self, request, pk=None):
        """
        Lay out one teacher's evening.

        Body: ``{"teacher": uuid, "start": iso, "end": iso,
        "duration_minutes": 10, "break_after": 6, "break_minutes": 10}``
        """
        from products.cyed.hr.models import Staff

        round_obj = self.get_object()
        teacher = Staff.objects.filter(
            tenant_id=request.tenant_id, id=request.data.get("teacher")
        ).first()
        if teacher is None:
            return Response({"detail": "teacher must be a staff member in this school."},
                            status=status.HTTP_400_BAD_REQUEST)

        from django.utils.dateparse import parse_datetime

        start = parse_datetime(request.data.get("start") or "")
        end = parse_datetime(request.data.get("end") or "")
        if not (start and end):
            return Response({"detail": "start and end must be ISO datetimes."},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            slots = interviews.generate_slots(
                round_obj, teacher=teacher, start=start, end=end,
                duration_minutes=int(request.data.get("duration_minutes", 10)),
                break_after=request.data.get("break_after"),
                break_minutes=int(request.data.get("break_minutes", 0)),
                location=request.data.get("location", ""),
            )
        except interviews.InterviewError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {"created": slots.count(), "teacher": str(teacher.id)},
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["get"])
    def slots(self, request, pk=None):
        """
        What a family can still book. `?teacher=<uuid>&student=<uuid>`

        A family's own bookings come back flagged rather than hidden, so they
        can see the evening take shape.
        """
        round_obj = self.get_object()
        student_id = request.query_params.get("student")

        visible = visible_student_ids(request, request.tenant_id)
        if visible is not None and student_id and str(student_id) not in {str(s) for s in visible}:
            return Response({"detail": "That is not your student."},
                            status=status.HTTP_403_FORBIDDEN)

        rows = interviews.available_slots(
            round_obj,
            teacher_id=request.query_params.get("teacher"),
            student_id=student_id,
        )
        return Response({"count": len(rows), "results": rows})

    @action(detail=True, methods=["get"], url_path="my-schedule")
    def my_schedule(self, request, pk=None):
        """
        The evening as it stands — a family's appointments, or a teacher's.

        Staff asking without naming a student get their own teaching schedule,
        which is what a teacher opening this page wants.
        """
        round_obj = self.get_object()
        student_id = request.query_params.get("student")

        if student_id:
            visible = visible_student_ids(request, request.tenant_id)
            if visible is not None and str(student_id) not in {str(s) for s in visible}:
                return Response({"detail": "That is not your student."},
                                status=status.HTTP_403_FORBIDDEN)
            return Response({
                "student": student_id,
                "appointments": interviews.schedule_for_student(round_obj, student_id),
            })

        if not is_staff(request):
            visible = visible_student_ids(request, request.tenant_id) or set()
            if len(visible) == 1:
                only = str(next(iter(visible)))
                return Response({
                    "student": only,
                    "appointments": interviews.schedule_for_student(round_obj, only),
                })
            return Response(
                {"detail": "Pass ?student=<uuid> — you have more than one child."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from products.cyed.hr.models import Staff

        staff = Staff.objects.filter(
            tenant_id=request.tenant_id, email__iexact=_email(request)
        ).first()
        if staff is None:
            return Response(
                {"detail": "No staff record is linked to this account's email."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(interviews.schedule_for_teacher(round_obj, staff.id))


class InterviewSlotViewSet(TenantScopedModelViewSet):
    """Individual appointment windows. Staff manage; families book via `book/`."""

    queryset = InterviewSlot.objects.select_related("teacher", "round").all()
    serializer_class = InterviewSlotSerializer

    def get_permissions(self):
        if self.action in ("book", "list", "retrieve"):
            return [IsAuthenticatedViaClaims()]
        return [IsStaff()]

    def get_queryset(self):
        qs = super().get_queryset()
        params = self.request.query_params
        if params.get("round"):
            qs = qs.filter(round_id=params["round"])
        if params.get("teacher"):
            qs = qs.filter(teacher_id=params["teacher"])
        if not is_staff(self.request):
            qs = qs.filter(round__is_published=True)
        return qs

    @action(detail=True, methods=["post"])
    def book(self, request, pk=None):
        """
        Take this slot. Body: ``{"student": uuid, "note": "..."}``

        A family may only book for their own child.
        """
        from products.cyed.sis.models import Student

        slot = self.get_object()
        student = Student.objects.filter(
            tenant_id=request.tenant_id, id=request.data.get("student")
        ).first()
        if student is None:
            return Response({"detail": "student is required."},
                            status=status.HTTP_400_BAD_REQUEST)

        visible = visible_student_ids(request, request.tenant_id)
        if visible is not None and student.id not in visible:
            return Response({"detail": "You can only book for your own child."},
                            status=status.HTTP_403_FORBIDDEN)

        session = getattr(request, "user_session", None) or {}
        try:
            booking = interviews.book(
                slot, student=student,
                booked_by_email=_email(request),
                booked_by_name=session.get("name", "") or _email(request),
                note=request.data.get("note", ""),
            )
        except interviews.InterviewError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_409_CONFLICT)

        return Response(InterviewBookingSerializer(booking).data,
                        status=status.HTTP_201_CREATED)


class InterviewBookingViewSet(TenantScopedModelViewSet):
    """
    Appointments. Created through `slots/{id}/book/` so the fairness and
    double-booking rules cannot be bypassed.
    """

    queryset = InterviewBooking.objects.select_related(
        "slot", "slot__teacher", "student"
    ).all()
    serializer_class = InterviewBookingSerializer
    permission_classes = [IsAuthenticatedViaClaims]
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self):
        qs = super().get_queryset()
        visible = visible_student_ids(self.request, self.request.tenant_id)
        if visible is not None:
            qs = qs.filter(student_id__in=visible)
        if self.request.query_params.get("round"):
            qs = qs.filter(slot__round_id=self.request.query_params["round"])
        return qs

    def create(self, request, *args, **kwargs):
        return Response(
            {"detail": "Book through /interview-slots/{id}/book/."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        """Free the slot. The row is kept — a cancellation is worth knowing about."""
        try:
            booking = interviews.cancel(self.get_object())
        except interviews.InterviewError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_409_CONFLICT)
        return Response(self.get_serializer(booking).data)

    @action(detail=True, methods=["post"], url_path="mark-attendance",
            permission_classes=[IsStaff])
    def mark_attendance(self, request, pk=None):
        booking = self.get_object()
        value = request.data.get("status")
        if value not in ("attended", "no_show"):
            return Response({"detail": "status must be 'attended' or 'no_show'."},
                            status=status.HTTP_400_BAD_REQUEST)
        booking.status = value
        booking.save(update_fields=["status", "updated_at"])
        return Response(self.get_serializer(booking).data)
