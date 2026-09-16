from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from products.cyed.governance.access import (
    ADMIN,
    LEADERSHIP,
    AuditedTenantViewSet,
    IsPastoralOrLeadership,
    IsStaff,
    _email,
    has_any,
)
from products.cyed.health import services
from products.cyed.health.models import (
    ActionPlan,
    HealthRecord,
    ImmunisationDose,
    ImmunisationRecord,
    MedicalIncident,
    MedicationAdministration,
    MedicationAuthority,
    SickBayVisit,
    VACCINE_PREVENTABLE,
)
from products.cyed.health.serializers import (
    ActionPlanSerializer,
    HealthRecordSerializer,
    ImmunisationDoseSerializer,
    ImmunisationRecordSerializer,
    MedicalIncidentSerializer,
    MedicationAdministrationSerializer,
    MedicationAuthoritySerializer,
    SickBayVisitSerializer,
)
from products.cyed.hr.models import Staff


class HealthRecordViewSet(AuditedTenantViewSet):
    """Confidential health data — pastoral/leadership only; every access audited."""

    queryset = HealthRecord.objects.select_related("student").all()
    serializer_class = HealthRecordSerializer
    permission_classes = [IsPastoralOrLeadership]

    def get_queryset(self):
        qs = super().get_queryset()
        student = self.request.query_params.get("student")
        if student:
            qs = qs.filter(student_id=student)
        return qs


class MedicalIncidentViewSet(AuditedTenantViewSet):
    queryset = MedicalIncident.objects.select_related("student").all()
    serializer_class = MedicalIncidentSerializer
    permission_classes = [IsPastoralOrLeadership]

    def get_queryset(self):
        qs = super().get_queryset()
        student = self.request.query_params.get("student")
        if student:
            qs = qs.filter(student_id=student)
        return qs


class SickBayVisitViewSet(AuditedTenantViewSet):
    """
    The sick bay log.

    Open a visit when a student arrives, close it with an outcome. Closing is
    what sends the guardian alert — there is no separate "did you ring them"
    checkbox, because that is what made the old field meaningless.
    """

    queryset = SickBayVisit.objects.select_related("student", "seen_by").all()
    serializer_class = SickBayVisitSerializer
    permission_classes = [IsStaff]

    def get_queryset(self):
        qs = super().get_queryset()
        params = self.request.query_params
        if params.get("student"):
            qs = qs.filter(student_id=params["student"])
        if params.get("open") == "1":
            qs = qs.filter(departed_at__isnull=True)
        if params.get("date"):
            qs = qs.filter(arrived_at__date=params["date"])
        return qs

    def perform_create(self, serializer):
        """Open a visit, defaulting the referring adult to whoever logged it."""
        serializer.save(
            tenant_id=self.request.tenant_id,
            referred_by=serializer.validated_data.get("referred_by") or _email(self.request),
        )

    @action(detail=False, methods=["get"])
    def current(self, request):
        """Who is in the sick bay right now."""
        rows = services.open_visits(
            request.tenant_id, campus_id=request.query_params.get("campus")
        )
        return Response({"count": len(rows), "results": rows})

    @action(detail=False, methods=["get"])
    def day(self, request):
        """Every visit for a day — the log a school produces when asked."""
        return Response(services.sick_bay_day(
            request.tenant_id, day=request.query_params.get("date")
        ))

    @action(detail=True, methods=["post"])
    def close(self, request, pk=None):
        """
        Close the visit.

        Body: ``{"outcome": "sent_home", "collected_by": "Hoa Tran",
        "treatment": "...", "observations": "...", "notify": true}``

        `sent_home` and `emergency` message the guardians automatically.
        """
        from products.cyed.hr.models import Staff

        seen_by = None
        if request.data.get("seen_by"):
            seen_by = Staff.objects.filter(
                tenant_id=request.tenant_id, id=request.data["seen_by"]
            ).first()

        try:
            visit = services.close_visit(
                self.get_object(),
                outcome=request.data.get("outcome", ""),
                treatment=request.data.get("treatment", ""),
                observations=request.data.get("observations", ""),
                collected_by=request.data.get("collected_by", ""),
                seen_by=seen_by,
                notify=bool(request.data.get("notify", True)),
            )
        except services.SickBayError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_409_CONFLICT)

        return Response({
            **self.get_serializer(visit).data,
            "guardians_notified": visit.guardians_notified,
        })

    @action(detail=True, methods=["post"], url_path="notify-guardians")
    def notify_guardians(self, request, pk=None):
        """
        Message the guardians without closing the visit — a child who might
        need collecting later, so the family can start moving now.
        """
        visit = self.get_object()
        sent = services.notify_guardians(visit, request.data.get("outcome", "sent_home"))
        visit.guardians_notified = visit.guardians_notified + sent
        visit.notified_at = timezone.now()
        visit.save(update_fields=["guardians_notified", "notified_at", "updated_at"])
        return Response({"notified": sent})


class ActionPlanViewSet(AuditedTenantViewSet):
    """
    Emergency medical plans — anaphylaxis, asthma, diabetes, seizure.

    Readable by any staff member, deliberately. Health data is otherwise
    pastoral-only, but a plan a relief teacher cannot open is a plan that fails
    at the moment it is needed. Every read is still audited, which is the
    control that makes the wider access defensible.
    """

    queryset = ActionPlan.objects.select_related("student").all()
    serializer_class = ActionPlanSerializer
    permission_classes = [IsStaff]

    def get_queryset(self):
        qs = super().get_queryset()
        params = self.request.query_params
        if params.get("student"):
            qs = qs.filter(student_id=params["student"])
        if params.get("plan_type"):
            qs = qs.filter(plan_type=params["plan_type"])
        if params.get("active") == "1":
            qs = qs.filter(is_active=True)
        return qs

    @action(detail=False, methods=["get"])
    def critical(self, request):
        """
        Every current life-threatening plan, ordered for a supervisor.

        Expired plans are listed with their status, not filtered out: a lapsed
        anaphylaxis plan is the most important thing on the page, and hiding it
        because the paperwork is overdue would be the worst possible reading of
        "current".
        """
        rows = services.critical_plans(
            request.tenant_id, campus_id=request.query_params.get("campus")
        )
        return Response({"count": len(rows), "results": rows})

    @action(detail=False, methods=["get"], url_path="needing-review")
    def needing_review(self, request):
        """Expired or soon-to-expire plans — the health office's chase list."""
        rows = services.plans_needing_review(request.tenant_id)
        return Response({"count": len(rows), "results": rows})

    @action(detail=False, methods=["get"], url_path="for-group")
    def for_group(self, request):
        """
        Plans for a class or an excursion party. `?students=a,b,c` or
        `?class_section=<uuid>`.

        What a teacher takes with them when they leave the site.
        """
        student_ids = None
        if request.query_params.get("class_section"):
            from products.cyed.sis.models import Enrolment

            student_ids = list(
                Enrolment.objects.filter(
                    tenant_id=request.tenant_id,
                    class_section_id=request.query_params["class_section"],
                    status="active",
                ).values_list("student_id", flat=True)
            )
        elif request.query_params.get("students"):
            student_ids = [s for s in request.query_params["students"].split(",") if s]

        if student_ids is None:
            return Response(
                {"detail": "Give ?class_section=<uuid> or ?students=<uuid>,<uuid>."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        rows = services.critical_plans(request.tenant_id, student_ids=student_ids)
        return Response({"count": len(rows), "results": rows})


class ImmunisationRecordViewSet(AuditedTenantViewSet):
    """
    The immunisation register: what the school can evidence about each child.

    Health data, so pastoral/leadership only and every read audited.
    """

    queryset = ImmunisationRecord.objects.select_related("student").prefetch_related("doses").all()
    serializer_class = ImmunisationRecordSerializer
    permission_classes = [IsPastoralOrLeadership]

    def get_queryset(self):
        qs = super().get_queryset()
        params = self.request.query_params
        if params.get("student"):
            qs = qs.filter(student_id=params["student"])
        if params.get("status"):
            qs = qs.filter(status=params["status"])
        return qs

    def perform_create(self, serializer):
        self._save_with_verification(serializer)

    def perform_update(self, serializer):
        self._save_with_verification(serializer)

    def _save_with_verification(self, serializer):
        """Stamp who sighted the AIR statement — the same rule as a clearance."""
        extra = {"tenant_id": self.request.tenant_id}
        if serializer.validated_data.get("verified_on"):
            extra["verified_by"] = _email(self.request)
        serializer.save(**extra)

    @action(detail=False, methods=["get"])
    def gaps(self, request):
        """
        Enrolled students whose immunisation evidence does not satisfy
        enrolment — including those with no record at all, which is the case a
        query over existing rows would silently miss.
        """
        rows = services.immunisation_gaps(
            request.tenant_id,
            campus_id=request.query_params.get("campus"),
            year_level=request.query_params.get("year_level"),
        )
        return Response({"count": len(rows), "results": rows})

    @action(detail=False, methods=["get"], url_path="outbreak-exclusions")
    def outbreak_exclusions(self, request):
        """
        Who must be kept away during an outbreak of a named disease.

        `?disease=measles`. A medical exemption is not protection here — an
        exempt child is exactly the one an exclusion directive protects.
        """
        disease = request.query_params.get("disease")
        valid = {code for code, _ in VACCINE_PREVENTABLE}
        if disease not in valid:
            return Response(
                {"detail": f"Unknown disease. Use one of: {', '.join(sorted(valid))}."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(services.outbreak_exclusion_list(
            request.tenant_id, disease, campus_id=request.query_params.get("campus")
        ))


class ImmunisationDoseViewSet(AuditedTenantViewSet):
    queryset = ImmunisationDose.objects.select_related("record").all()
    serializer_class = ImmunisationDoseSerializer
    permission_classes = [IsPastoralOrLeadership]

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.query_params.get("record"):
            qs = qs.filter(record_id=self.request.query_params["record"])
        return qs


class MedicationAuthorityViewSet(AuditedTenantViewSet):
    """Standing authorisations to administer a medication to a named student."""

    queryset = MedicationAuthority.objects.select_related("student", "authorised_by").all()
    serializer_class = MedicationAuthoritySerializer
    permission_classes = [IsPastoralOrLeadership]

    def get_queryset(self):
        qs = super().get_queryset()
        params = self.request.query_params
        if params.get("student"):
            qs = qs.filter(student_id=params["student"])
        if params.get("current") == "1":
            qs = qs.filter(is_active=True)
        return qs

    @action(detail=False, methods=["get"], url_path="due-today")
    def due_today(self, request):
        """
        The first-aid room's worklist: current authorities and how many doses
        have already gone out today.
        """
        rows = services.medication_due_today(
            request.tenant_id, campus_id=request.query_params.get("campus")
        )
        return Response({"count": len(rows), "date": timezone.localdate(), "results": rows})

    @action(detail=True, methods=["post"])
    def administer(self, request, pk=None):
        """
        Record a dose against this authority.

        Body: ``{"administered_by": "<staff uuid>", "dose_given": "2 puffs",
        "outcome": "given", "witnessed_by": "<staff uuid>",
        "self_administered": false, "notes": "", "override_reason": ""}``

        Refuses a dose that the authority does not permit — expired, over the
        daily maximum, or inside the minimum interval. Leadership may override
        with a recorded reason (a prescriber authorising an extra dose by phone
        is a real situation), but never silently.

        Recording a refusal or an omission is always allowed: those are the
        events a duty-of-care log exists to capture.
        """
        authority = self.get_object()
        staff_id = request.data.get("administered_by")
        staff = Staff.objects.filter(tenant_id=request.tenant_id, id=staff_id).first() if staff_id else None
        if staff is None:
            return Response(
                {"detail": "administered_by must be a staff member in this school."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        witness = None
        if request.data.get("witnessed_by"):
            witness = Staff.objects.filter(
                tenant_id=request.tenant_id, id=request.data["witnessed_by"]
            ).first()
            if witness is None:
                return Response({"detail": "witnessed_by must be a staff member in this school."},
                                status=status.HTTP_400_BAD_REQUEST)

        override_reason = (request.data.get("override_reason") or "").strip()
        if override_reason and not has_any(request, ADMIN | LEADERSHIP):
            return Response(
                {"detail": "Only leadership may override a medication limit."},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            record = services.administer(
                authority=authority,
                administered_by=staff,
                dose_given=request.data.get("dose_given", ""),
                outcome=request.data.get("outcome", "given"),
                witnessed_by=witness,
                self_administered=bool(request.data.get("self_administered")),
                notes=request.data.get("notes", ""),
                override_reason=override_reason,
                override_by=_email(request) if override_reason else "",
            )
        except services.MedicationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_409_CONFLICT)

        return Response(
            MedicationAdministrationSerializer(record).data, status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=["get"], url_path="check")
    def check(self, request, pk=None):
        """Would a dose right now be permitted? Lets a UI warn before the click."""
        return Response(services.check_dose(self.get_object()))


class MedicationAdministrationViewSet(AuditedTenantViewSet):
    """
    The medication administration log — read-only over the API.

    Doses are written through `medication-authorities/{id}/administer/` so the
    safety checks cannot be bypassed by posting a row directly, and nothing is
    editable afterwards: a duty-of-care record that can be amended in place is
    not evidence of what happened.
    """

    queryset = MedicationAdministration.objects.select_related(
        "authority", "student", "administered_by", "witnessed_by"
    ).all()
    serializer_class = MedicationAdministrationSerializer
    permission_classes = [IsPastoralOrLeadership]
    http_method_names = ["get", "head", "options"]

    def get_queryset(self):
        qs = super().get_queryset()
        params = self.request.query_params
        if params.get("student"):
            qs = qs.filter(student_id=params["student"])
        if params.get("date"):
            qs = qs.filter(administered_on=params["date"])
        if params.get("outcome"):
            qs = qs.filter(outcome=params["outcome"])
        return qs
