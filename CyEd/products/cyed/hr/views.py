from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from core.viewsets import TenantScopedModelViewSet
from products.cyed.governance.access import (
    ADMIN, LEADERSHIP, CampusScopedMixin, IsStaff, _email, has_any,
)
from products.cyed.hr import compliance
from products.cyed.hr.models import (
    Contract, LeaveEntitlement, OnboardingTask, PerformanceReview, Staff, StaffClearance, StaffLeave,
)
from products.cyed.hr.serializers import (
    ContractSerializer, LeaveEntitlementSerializer, OnboardingTaskSerializer,
    PerformanceReviewSerializer, StaffClearanceSerializer, StaffLeaveSerializer, StaffSerializer,
)

# Default checklists used when kicking off a workflow. Kept in code (not data)
# so a new tenant gets a sane baseline with no configuration.
ONBOARDING_CHECKLIST = [
    "Verify Working With Children Check",
    "Collect Tax File Number declaration",
    "Collect superannuation choice form",
    "Issue email account and system access",
    "Issue laptop / equipment",
    "Site induction and emergency procedures",
    "Sign employment contract",
]
OFFBOARDING_CHECKLIST = [
    "Revoke system and email access",
    "Return laptop / equipment",
    "Return keys and access card",
    "Final pay and leave payout calculated",
    "Exit interview completed",
    "Handover documented",
]


class StaffViewSet(CampusScopedMixin, TenantScopedModelViewSet):
    # Clearances are prefetched because every staff row reports `may_teach`,
    # which reads them — without this the list is one query per staff member.
    queryset = Staff.objects.prefetch_related("clearances").all()
    serializer_class = StaffSerializer
    permission_classes = [IsStaff]

    @action(detail=False, methods=["post"], url_path="import")
    def bulk_import(self, request):
        """Data-migration import: POST a CSV (multipart field `file`) to bulk
        create/update staff. Returns a per-row report."""
        upload = request.FILES.get("file")
        if upload is None:
            return Response({"detail": "Attach a CSV as form field 'file'."}, status=400)
        from products.cyed.sis.imports import import_staff

        report = import_staff(request.tenant_id, upload.read())
        return Response(report)

    def _kickoff(self, request, staff, kind, checklist):
        existing = set(
            OnboardingTask.objects.filter(tenant_id=request.tenant_id, staff=staff, kind=kind)
            .values_list("title", flat=True)
        )
        created = [
            OnboardingTask.objects.create(
                tenant_id=request.tenant_id, staff=staff, kind=kind, title=title, sequence=i + 1,
                assigned_to=_email(request),
            )
            for i, title in enumerate(checklist)
            if title not in existing  # idempotent: re-running never duplicates
        ]
        return created

    @action(detail=True, methods=["post"])
    def onboard(self, request, pk=None):
        """Start onboarding: create the standard checklist for this staff member."""
        staff = self.get_object()
        created = self._kickoff(request, staff, "onboarding", ONBOARDING_CHECKLIST)
        return Response({
            "staff": str(staff.id), "kind": "onboarding", "tasks_created": len(created),
            "tasks": OnboardingTaskSerializer(
                OnboardingTask.objects.filter(tenant_id=request.tenant_id, staff=staff, kind="onboarding"),
                many=True,
            ).data,
        })

    @action(detail=True, methods=["post"])
    def offboard(self, request, pk=None):
        """
        Start offboarding: create the exit checklist, end the current contract,
        and deactivate the staff record. Leadership only.
        """
        if not has_any(request, ADMIN | LEADERSHIP):
            return Response({"detail": "Only leadership may offboard staff."},
                            status=status.HTTP_403_FORBIDDEN)
        staff = self.get_object()
        created = self._kickoff(request, staff, "offboarding", OFFBOARDING_CHECKLIST)
        end_date = request.data.get("end_date") or timezone.localdate().isoformat()
        Contract.objects.filter(tenant_id=request.tenant_id, staff=staff, is_current=True).update(
            is_current=False, end_date=end_date
        )
        staff.is_active = False
        staff.save(update_fields=["is_active", "updated_at"])
        return Response({
            "staff": str(staff.id), "kind": "offboarding", "tasks_created": len(created),
            "is_active": staff.is_active, "contracts_ended": True, "end_date": end_date,
        })


class StaffClearanceViewSet(TenantScopedModelViewSet):
    """
    WWCC, teacher registration and the other credentials a school must monitor.

    Staff-only, and deliberately not self-service: verification is someone
    sighting the card against the regulator's register, so a person cannot
    record their own clearance as verified.
    """

    queryset = StaffClearance.objects.select_related("staff").all()
    serializer_class = StaffClearanceSerializer
    permission_classes = [IsStaff]

    def get_queryset(self):
        qs = super().get_queryset()
        params = self.request.query_params
        if params.get("staff"):
            qs = qs.filter(staff_id=params["staff"])
        if params.get("kind"):
            qs = qs.filter(kind=params["kind"])
        return qs

    def perform_create(self, serializer):
        self._save_with_verification(serializer)

    def perform_update(self, serializer):
        self._save_with_verification(serializer)

    def _save_with_verification(self, serializer):
        """
        Record who verified the credential, and when.

        Only leadership may attest — the whole value of the record is that a
        responsible person sighted the document, and letting the subject set
        their own `verified_on` would make the field worthless as evidence.
        """
        data = dict(serializer.validated_data)
        if data.get("verified_on") and not has_any(self.request, ADMIN | LEADERSHIP):
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("Only leadership may mark a clearance as verified.")
        extra = {"tenant_id": self.request.tenant_id}
        if data.get("verified_on"):
            extra["verified_by"] = _email(self.request)
        serializer.save(**extra)

    @action(detail=False, methods=["get"])
    def expiring(self, request):
        """Lapsed, unverified, or about to lapse — the registrar's worklist."""
        within = int(request.query_params.get("within_days", StaffClearance.EXPIRY_WARNING_DAYS))
        rows = compliance.expiring_clearances(request.tenant_id, within_days=within)
        return Response({"count": len(rows), "within_days": within, "results": rows})

    @action(detail=False, methods=["get"], url_path="blocked-from-teaching")
    def blocked(self, request):
        """
        Active staff who may not be with students right now.

        Each row is a class that needs covering — this is the list a principal
        needs before Monday, not a compliance report for the end of term.
        """
        rows = compliance.staff_blocked_from_teaching(request.tenant_id)
        return Response({"count": len(rows), "results": rows})


class LeaveEntitlementViewSet(TenantScopedModelViewSet):
    queryset = LeaveEntitlement.objects.select_related("staff").all()
    serializer_class = LeaveEntitlementSerializer
    permission_classes = [IsStaff]

    def get_queryset(self):
        qs = super().get_queryset()
        params = self.request.query_params
        if params.get("staff"):
            qs = qs.filter(staff_id=params["staff"])
        if params.get("year"):
            qs = qs.filter(year=params["year"])
        return qs

    @action(detail=False, methods=["post"], url_path="open-year")
    def open_year(self, request):
        """
        Create annual and personal-leave entitlements for a leave year.

        Pro-rated by each contract's FTE; casuals get nothing, because under
        the NES they are paid a loading in lieu of paid leave. Idempotent, so
        running it twice on 1 January is harmless and a hand-adjusted
        entitlement is never overwritten.
        """
        if not has_any(request, ADMIN | LEADERSHIP):
            return Response({"detail": "Only leadership may open a leave year."},
                            status=status.HTTP_403_FORBIDDEN)
        year = int(request.data.get("year") or timezone.localdate().year)
        created = 0
        for staff in Staff.objects.filter(tenant_id=request.tenant_id, is_active=True):
            created += len(compliance.ensure_entitlements(staff, year))
        return Response({"year": year, "entitlements_created": created})

    @action(detail=False, methods=["get"])
    def balances(self, request):
        """
        Leave balances for one staff member — the answer to "do I have leave
        left?", derived rather than stored so it cannot drift.
        """
        staff_id = request.query_params.get("staff")
        if not staff_id:
            return Response({"detail": "staff is required."}, status=status.HTTP_400_BAD_REQUEST)
        staff = Staff.objects.filter(tenant_id=request.tenant_id, id=staff_id).first()
        if staff is None:
            return Response({"detail": "No such staff member."}, status=status.HTTP_404_NOT_FOUND)
        year = request.query_params.get("year")
        return Response(compliance.leave_balances(staff, year=int(year) if year else None))


class ContractViewSet(TenantScopedModelViewSet):
    queryset = Contract.objects.select_related("staff").all()
    serializer_class = ContractSerializer
    permission_classes = [IsStaff]

    def get_queryset(self):
        qs = super().get_queryset()
        staff = self.request.query_params.get("staff")
        return qs.filter(staff_id=staff) if staff else qs


class StaffLeaveViewSet(TenantScopedModelViewSet):
    queryset = StaffLeave.objects.select_related("staff").all()
    serializer_class = StaffLeaveSerializer
    permission_classes = [IsStaff]

    def get_queryset(self):
        qs = super().get_queryset()
        staff = self.request.query_params.get("staff")
        if self.request.query_params.get("status"):
            qs = qs.filter(status=self.request.query_params["status"])
        return qs.filter(staff_id=staff) if staff else qs

    def _decide(self, request, decision):
        if not has_any(request, ADMIN | LEADERSHIP):
            return Response({"detail": "Only leadership may decide leave requests."},
                            status=status.HTTP_403_FORBIDDEN)
        leave = self.get_object()
        if leave.status != "requested":
            return Response({"detail": f"Leave is already '{leave.status}'."}, status=400)

        if decision == "approved":
            verdict = compliance.check_leave_balance(leave)
            if verdict["applicable"] and not verdict["sufficient"]:
                # Leadership may still approve — an employee taking leave in
                # advance of accrual is a normal arrangement — but it has to be
                # a deliberate, attributable act. An override with no reason is
                # indistinguishable from a bug six months later.
                override = (request.data.get("override_reason") or "").strip()
                if not override:
                    return Response(
                        {
                            "detail": (
                                f"Insufficient leave balance. {verdict['reason']} "
                                f"Approve anyway by supplying 'override_reason'."
                            ),
                            "balance": verdict,
                        },
                        status=status.HTTP_409_CONFLICT,
                    )
                leave.balance_override_by = _email(request)
                leave.balance_override_reason = override[:255]

        leave.status = decision
        leave.save()
        # An approved leave day should show up in staff attendance so payroll
        # treats it as paid-not-worked rather than an unexplained absence.
        if decision == "approved" and leave.start_date and leave.end_date:
            from datetime import timedelta

            from products.cyed.staff_attendance.models import StaffAttendanceDay

            kind = "sick" if leave.leave_type == "sick" else "leave"
            day = leave.start_date
            while day <= leave.end_date:
                if day.weekday() < 5:  # skip weekends
                    StaffAttendanceDay.objects.update_or_create(
                        tenant_id=leave.tenant_id, staff=leave.staff, date=day,
                        defaults={"status": kind, "leave_request": leave,
                                  "note": f"{leave.get_leave_type_display()} (approved)"},
                    )
                day += timedelta(days=1)
        return Response(StaffLeaveSerializer(leave).data)

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        return self._decide(request, "approved")

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        return self._decide(request, "rejected")


class PerformanceReviewViewSet(TenantScopedModelViewSet):
    queryset = PerformanceReview.objects.select_related("staff").all()
    serializer_class = PerformanceReviewSerializer
    permission_classes = [IsStaff]

    def get_queryset(self):
        qs = super().get_queryset()
        # Reviews are confidential: staff see only their own unless leadership.
        if not has_any(self.request, ADMIN | LEADERSHIP):
            email = _email(self.request)
            qs = qs.filter(staff__email__iexact=email) if email else qs.none()
        if self.request.query_params.get("staff"):
            qs = qs.filter(staff_id=self.request.query_params["staff"])
        return qs

    def get_permissions(self):
        # Only leadership may author or amend a review; staff may read + acknowledge.
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [IsStaff()]
        return [IsStaff()]

    def perform_create(self, serializer):
        if not has_any(self.request, ADMIN | LEADERSHIP):
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("Only leadership may create performance reviews.")
        serializer.save(tenant_id=self.request.tenant_id, reviewer_name=_email(self.request))

    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        if not has_any(request, ADMIN | LEADERSHIP):
            return Response({"detail": "Only leadership may submit a review."}, status=403)
        review = self.get_object()
        if review.overall_rating is None:
            return Response({"overall_rating": "Set a rating before submitting."}, status=400)
        review.status = "submitted"
        review.save()
        return Response(PerformanceReviewSerializer(review).data)

    @action(detail=True, methods=["post"])
    def acknowledge(self, request, pk=None):
        """The reviewed staff member acknowledges having read the review."""
        review = self.get_object()
        if review.status != "submitted":
            return Response({"detail": "Only a submitted review can be acknowledged."}, status=400)
        if (review.staff.email or "").lower() != (_email(request) or "").lower():
            return Response({"detail": "Only the reviewed staff member may acknowledge this review."},
                            status=status.HTTP_403_FORBIDDEN)
        review.status = "acknowledged"
        review.acknowledged_at = timezone.now()
        review.staff_comment = (request.data.get("staff_comment") or review.staff_comment)
        review.save()
        return Response(PerformanceReviewSerializer(review).data)


class OnboardingTaskViewSet(TenantScopedModelViewSet):
    queryset = OnboardingTask.objects.select_related("staff").all()
    serializer_class = OnboardingTaskSerializer
    permission_classes = [IsStaff]

    def get_queryset(self):
        qs = super().get_queryset()
        params = self.request.query_params
        if params.get("staff"):
            qs = qs.filter(staff_id=params["staff"])
        if params.get("kind"):
            qs = qs.filter(kind=params["kind"])
        if params.get("open") == "1":
            qs = qs.filter(is_completed=False)
        return qs

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        task = self.get_object()
        if task.is_completed:
            return Response({"detail": "Task is already complete."}, status=400)
        task.is_completed = True
        task.completed_at = timezone.now()
        task.completed_by = _email(request)
        task.save()
        return Response(OnboardingTaskSerializer(task).data)
