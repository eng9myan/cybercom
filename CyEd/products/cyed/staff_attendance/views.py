from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from core.viewsets import TenantScopedModelViewSet
from products.cyed.governance.access import (
    ADMIN, LEADERSHIP, IsStaff, _email, has_any,
)
from products.cyed.staff_attendance.models import StaffAttendanceDay, Timesheet
from products.cyed.staff_attendance.serializers import StaffAttendanceDaySerializer, TimesheetSerializer


def _own_staff(request):
    """The Staff row belonging to the caller, matched on email, or None."""
    from products.cyed.hr.models import Staff

    email = _email(request)
    if not email:
        return None
    return Staff.objects.filter(tenant_id=request.tenant_id, email__iexact=email).first()


class StaffAttendanceDayViewSet(TenantScopedModelViewSet):
    """
    Daily staff attendance. Staff see their own record; leadership/admin see all.
    Self-service check-in/check-out live here so a staff member never needs write
    access to anyone else's row.
    """

    queryset = StaffAttendanceDay.objects.select_related("staff").all()
    serializer_class = StaffAttendanceDaySerializer
    permission_classes = [IsStaff]

    def get_queryset(self):
        qs = super().get_queryset()
        if not has_any(self.request, ADMIN | LEADERSHIP):
            mine = _own_staff(self.request)
            qs = qs.filter(staff=mine) if mine else qs.none()
        params = self.request.query_params
        if params.get("staff"):
            qs = qs.filter(staff_id=params["staff"])
        if params.get("from"):
            qs = qs.filter(date__gte=params["from"])
        if params.get("to"):
            qs = qs.filter(date__lte=params["to"])
        if params.get("status"):
            qs = qs.filter(status=params["status"])
        return qs

    def _punch(self, request, field):
        staff = _own_staff(request)
        if staff is None:
            return Response(
                {"detail": "No staff record is linked to your account (email must match a Staff record)."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        today = timezone.localdate()
        now = timezone.localtime().time().replace(microsecond=0)
        day, _ = StaffAttendanceDay.objects.get_or_create(
            tenant_id=request.tenant_id, staff=staff, date=today,
            defaults={"scheduled_start": request.data.get("scheduled_start") or None},
        )
        if getattr(day, field) is not None:
            return Response({"detail": f"Already recorded a {field.replace('_', '-')} for today."},
                            status=status.HTTP_400_BAD_REQUEST)
        if field == "check_out" and day.check_in is None:
            return Response({"detail": "Cannot check out before checking in."},
                            status=status.HTTP_400_BAD_REQUEST)
        setattr(day, field, now)
        day.save()
        return Response(StaffAttendanceDaySerializer(day).data)

    @action(detail=False, methods=["post"], url_path="check-in")
    def check_in_action(self, request):
        return self._punch(request, "check_in")

    @action(detail=False, methods=["post"], url_path="check-out")
    def check_out_action(self, request):
        return self._punch(request, "check_out")

    @action(detail=False, methods=["get"], url_path="today")
    def today(self, request):
        staff = _own_staff(request)
        if staff is None:
            return Response({"detail": "No staff record linked to your account."}, status=400)
        day = StaffAttendanceDay.objects.filter(
            tenant_id=request.tenant_id, staff=staff, date=timezone.localdate()
        ).first()
        return Response(StaffAttendanceDaySerializer(day).data if day else {"detail": "Not checked in yet."})

    @action(detail=False, methods=["get"], url_path="summary")
    def summary(self, request):
        """Lateness / absence roll-up per staff member over a date range."""
        if not has_any(request, ADMIN | LEADERSHIP):
            return Response({"detail": "Leadership only."}, status=status.HTTP_403_FORBIDDEN)
        qs = StaffAttendanceDay.objects.filter(tenant_id=request.tenant_id).select_related("staff")
        if request.query_params.get("from"):
            qs = qs.filter(date__gte=request.query_params["from"])
        if request.query_params.get("to"):
            qs = qs.filter(date__lte=request.query_params["to"])
        rows: dict = {}
        for d in qs:
            r = rows.setdefault(
                str(d.staff_id),
                {"staff": str(d.staff_id), "name": f"{d.staff.first_name} {d.staff.last_name}",
                 "days": 0, "present": 0, "absent": 0, "leave": 0, "late": 0,
                 "minutes_late": 0, "hours": 0.0},
            )
            r["days"] += 1
            if d.status in ("present", "late"):
                r["present"] += 1
            if d.status == "absent":
                r["absent"] += 1
            if d.status in ("leave", "sick"):
                r["leave"] += 1
            if d.minutes_late:
                r["late"] += 1
                r["minutes_late"] += d.minutes_late
            r["hours"] += float(d.hours_worked)
        return Response({"count": len(rows), "rows": sorted(rows.values(), key=lambda x: -x["absent"])})


class TimesheetViewSet(TenantScopedModelViewSet):
    queryset = Timesheet.objects.select_related("staff").all()
    serializer_class = TimesheetSerializer
    permission_classes = [IsStaff]

    def get_queryset(self):
        qs = super().get_queryset()
        if not has_any(self.request, ADMIN | LEADERSHIP):
            mine = _own_staff(self.request)
            qs = qs.filter(staff=mine) if mine else qs.none()
        if self.request.query_params.get("staff"):
            qs = qs.filter(staff_id=self.request.query_params["staff"])
        return qs

    def perform_create(self, serializer):
        serializer.save(tenant_id=self.request.tenant_id).recalculate()

    @action(detail=True, methods=["post"])
    def recalculate(self, request, pk=None):
        ts = self.get_object()
        ts.recalculate()
        return Response(TimesheetSerializer(ts).data)

    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        ts = self.get_object()
        if ts.status == "approved":
            return Response({"detail": "An approved timesheet cannot be resubmitted."}, status=400)
        ts.recalculate()
        ts.status = "submitted"
        ts.save()
        return Response(TimesheetSerializer(ts).data)

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        if not has_any(request, ADMIN | LEADERSHIP):
            return Response({"detail": "Only leadership may approve timesheets."},
                            status=status.HTTP_403_FORBIDDEN)
        ts = self.get_object()
        if ts.status != "submitted":
            return Response({"detail": "Only a submitted timesheet can be approved."}, status=400)
        ts.status = "approved"
        ts.approved_by = _email(request)
        ts.save()
        return Response(TimesheetSerializer(ts).data)
