from django.db.models import Q
from rest_framework.decorators import action
from rest_framework.response import Response

from core.viewsets import TenantScopedModelViewSet
from products.cyed.governance.access import _email, is_staff, visible_student_ids
from products.cyed.timetable.models import TimetableSlot
from products.cyed.timetable.serializers import TimetableSlotSerializer


class TimetableSlotViewSet(TenantScopedModelViewSet):
    queryset = TimetableSlot.objects.select_related("class_section", "teacher", "class_section__teacher").all()
    serializer_class = TimetableSlotSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        params = self.request.query_params
        class_section = params.get("class_section")
        day = params.get("day_of_week")
        if class_section:
            qs = qs.filter(class_section_id=class_section)
        if day:
            qs = qs.filter(day_of_week=day)
        return qs

    @action(detail=False, methods=["get"], url_path="mine")
    def mine(self, request):
        """
        "What is my timetable?" — answered for whoever is asking.

        A teacher gets the classes they take: a slot counts as theirs if it
        carries their `teacher` FK directly (a cover or split-class override),
        or if the slot has no override and the parent section's teacher is them.

        A student gets the classes they are enrolled in. A parent gets their
        children's, and must name one with `?student=<uuid>` when they have
        more than one — guessing which child they meant would be worse than
        asking.
        """
        email = _email(request)
        if not email:
            return Response([])

        # An explicitly named student wins over the caller's role. Staff need
        # this to look at a child's day (and to preview the family portal), and
        # without it a staff account asking for one student's timetable gets
        # their own teaching load instead — or, having no Staff record, an
        # error about staff records on a family-facing screen.
        if request.query_params.get("student"):
            return self._student_timetable(request)
        if is_staff(request):
            return self._teacher_timetable(request, email)
        return self._student_timetable(request)

    def _teacher_timetable(self, request, email):
        from products.cyed.hr.models import Staff

        staff = Staff.objects.filter(tenant_id=request.tenant_id, email__iexact=email).first()
        if not staff:
            return Response(
                {"detail": "No staff record linked to this account's email."}, status=404
            )
        qs = self.get_queryset().filter(
            Q(teacher=staff) | Q(teacher__isnull=True, class_section__teacher=staff)
        )
        return Response(self.get_serializer(qs, many=True).data)

    def _student_timetable(self, request):
        from products.cyed.sis.models import Enrolment  # noqa: F401 — used below

        visible = visible_student_ids(request, request.tenant_id)
        requested = request.query_params.get("student")

        if visible is None:
            # Staff: unrestricted, but they must name a student — falling
            # through to the unscoped queryset would return the whole school's
            # timetable as if it were one child's.
            if not requested:
                return Response(
                    {"detail": "Staff must pass ?student=<uuid> to view a student's timetable."},
                    status=400,
                )
            student_ids = [requested]
            section_ids = Enrolment.objects.filter(
                tenant_id=request.tenant_id, student_id__in=student_ids, status="active"
            ).values_list("class_section_id", flat=True)
            return Response(
                self.get_serializer(
                    self.get_queryset().filter(class_section_id__in=section_ids), many=True
                ).data
            )

        if requested:
            if str(requested) not in {str(s) for s in visible}:
                return Response({"detail": "That is not your student."}, status=403)
            student_ids = [requested]
        elif not visible:
            # A family account with no children linked yet. Empty, not an error:
            # asking them to pick a student when they have none is nonsense.
            return Response([])
        elif len(visible) == 1:
            student_ids = list(visible)
        else:
            return Response(
                {
                    "detail": "You have more than one student. Pass ?student=<uuid>.",
                    "students": [str(s) for s in visible],
                },
                status=400,
            )

        section_ids = Enrolment.objects.filter(
            tenant_id=request.tenant_id, student_id__in=student_ids, status="active"
        ).values_list("class_section_id", flat=True)
        qs = self.get_queryset().filter(class_section_id__in=section_ids)
        return Response(self.get_serializer(qs, many=True).data)
