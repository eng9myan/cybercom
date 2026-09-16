from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from core.permissions import IsAuthenticatedViaClaims
from core.viewsets import TenantScopedModelViewSet
from products.cyed.governance.access import (
    AuditedTenantViewSet,
    CampusScopedMixin,
    IsStaff,
    IsStaffOrParent,
    _email,
    scope_queryset_by_student,
    visible_student_ids,
    write_audit,
)
from products.cyed.sis.models import (
    AcademicYear,
    ClassSection,
    Enrolment,
    Family,
    Guardian,
    Student,
)
from products.cyed.sis.serializers import (
    AcademicYearSerializer,
    ClassSectionSerializer,
    EnrolmentSerializer,
    FamilySerializer,
    GuardianSerializer,
    StudentSerializer,
)


class AcademicYearViewSet(TenantScopedModelViewSet):
    queryset = AcademicYear.objects.all()
    serializer_class = AcademicYearSerializer


class GuardianViewSet(TenantScopedModelViewSet):
    queryset = Guardian.objects.all()
    serializer_class = GuardianSerializer
    permission_classes = [IsStaff]


class FamilyViewSet(TenantScopedModelViewSet):
    """
    Household records.

    Staff see every household. A parent sees exactly one — their own — because
    it is their address and their billing contact, and the parent portal's fee
    statement is keyed on it. Locking parents out entirely made their own fees
    page unusable.

    Writes stay staff-only: a household's membership and billing contact decide
    who is invoiced and who may collect a child, so they are not a parent's to
    edit from the portal.

    The *money* view of a household (statement, sibling discounts, defaulter
    case) lives in billing and is scoped there.
    """

    queryset = Family.objects.select_related("billing_contact").prefetch_related("students").all()
    serializer_class = FamilySerializer

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [IsStaffOrParent()]
        return [IsStaff()]

    def get_queryset(self):
        qs = super().get_queryset()
        # A parent's queryset is narrowed to the households their children
        # belong to, so a direct id lookup 404s the same as a list omits it.
        visible = visible_student_ids(self.request, self.request.tenant_id)
        if visible is not None:
            qs = qs.filter(students__id__in=visible).distinct()
        student = self.request.query_params.get("student")
        if student:
            qs = qs.filter(students__id=student).distinct()
        return qs

    @action(detail=True, methods=["post"], url_path="members")
    def members(self, request, pk=None):
        """
        Attach students and/or guardians to this household.

        Body: {"students": [uuid, ...], "guardians": [uuid, ...]}. Ids from
        another tenant are rejected rather than silently ignored, so a bad
        import cannot quietly merge two schools' households.
        """
        family = self.get_object()
        tenant = request.tenant_id
        student_ids = request.data.get("students") or []
        guardian_ids = request.data.get("guardians") or []
        if not isinstance(student_ids, list) or not isinstance(guardian_ids, list):
            return Response({"detail": "'students' and 'guardians' must be lists of ids."},
                            status=400)

        students = list(Student.objects.filter(tenant_id=tenant, id__in=student_ids))
        guardians = list(Guardian.objects.filter(tenant_id=tenant, id__in=guardian_ids))
        if len(students) != len(set(map(str, student_ids))):
            return Response({"detail": "One or more students were not found in this tenant."},
                            status=400)
        if len(guardians) != len(set(map(str, guardian_ids))):
            return Response({"detail": "One or more guardians were not found in this tenant."},
                            status=400)

        for s in students:
            s.family = family
            s.save(update_fields=["family", "updated_at"])
        for g in guardians:
            g.family = family
            g.save(update_fields=["family", "updated_at"])
        write_audit(request, "update", family)

        # Membership decides sibling ordinals, and ordinals decide price — so
        # attaching a child re-prices their siblings, not just them. Imported
        # late to keep sis independent of billing at module load.
        from products.cyed.billing.family_accounts import resync_family

        bills_updated = resync_family(family)

        body = self.get_serializer(family).data
        body["bills_updated"] = bills_updated
        return Response(body)


class StudentViewSet(CampusScopedMixin, AuditedTenantViewSet):
    queryset = Student.objects.prefetch_related("guardians").all()
    serializer_class = StudentSerializer

    def get_permissions(self):
        # Read is available to any authenticated user but the queryset is scoped
        # (parents see only their children; students see themselves). All writes
        # and the export/de-identify actions are staff-only.
        if self.action in ("list", "retrieve"):
            return [IsAuthenticatedViaClaims()]
        return [IsStaff()]

    def get_queryset(self):
        # Campus scoping comes from the mixin via super(); student scoping
        # narrows further for parents and students. Both apply — a parent at
        # one campus of a group must not see another campus, and a campus
        # receptionist must not see a child at a site they do not work at.
        qs = super().get_queryset()
        return scope_queryset_by_student(self.request, self.request.tenant_id, qs, student_path="id")

    @action(detail=True, methods=["get"], url_path="exit-checks")
    def exit_checks(self, request, pk=None):
        """What still stands between this student and a clean exit."""
        from products.cyed.sis.lifecycle import exit_checks

        return Response(exit_checks(self.get_object()))

    @action(detail=True, methods=["post"], url_path="exit")
    def exit_student(self, request, pk=None):
        """
        Close a student's enrolment properly.

        Body: ``{"reason": "Family relocated", "destination": "Northside High",
        "graduated": false, "exit_date": "2026-12-12", "override_reason": ""}``

        Ends class enrolments, cancels transport, and closes the household's
        dunning case if this was the last child. Outstanding fees or library
        books block the exit unless an override reason is supplied.
        """
        from products.cyed.sis.lifecycle import LifecycleError, exit_student

        try:
            student = exit_student(
                self.get_object(),
                reason=request.data.get("reason", ""),
                exit_date=request.data.get("exit_date") or None,
                destination=request.data.get("destination", ""),
                actor=_email(request),
                graduated=bool(request.data.get("graduated")),
                override_reason=(request.data.get("override_reason") or "").strip(),
            )
        except LifecycleError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_409_CONFLICT)
        write_audit(request, "update", student)
        return Response(self.get_serializer(student).data)

    @action(detail=True, methods=["post"], url_path="transfer-certificate")
    def transfer_certificate(self, request, pk=None):
        """
        Issue the certificate a receiving school asks for.

        Refused while fees or library books are outstanding unless overridden —
        the certificate asserts the student left in good standing.
        """
        from products.cyed.sis.lifecycle import LifecycleError, issue_transfer_certificate

        try:
            certificate = issue_transfer_certificate(
                self.get_object(),
                actor=_email(request),
                notes=request.data.get("notes", ""),
                override_reason=(request.data.get("override_reason") or "").strip(),
            )
        except LifecycleError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_409_CONFLICT)
        return Response(
            {
                "certificate": str(certificate.id),
                "number": certificate.number,
                "version": certificate.version,
                "issued_on": certificate.issued_on,
                "fees_settled": certificate.fees_settled,
                "snapshot": certificate.snapshot,
            },
            status=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=["get"])
    def alumni(self, request):
        """Former students, most recent leavers first."""
        from products.cyed.sis.lifecycle import alumni

        rows = alumni(
            request.tenant_id,
            year=request.query_params.get("year"),
            year_level=request.query_params.get("year_level"),
        )
        return Response({"count": len(rows), "results": rows})

    @action(detail=True, methods=["post"], url_path="transfer-campus")
    def transfer_campus(self, request, pk=None):
        """
        Move this student to another campus in the group.

        Body: ``{"to_campus": "<uuid>", "effective_on": "2026-07-21",
        "reason": "Family relocated"}``

        Ends their class placements at the campus they are leaving — a section
        belongs to a campus, so carrying the placement across would leave them
        on a roll at a site they no longer attend. Re-placement is deliberate.
        """
        from products.cyed.org.models import Campus
        from products.cyed.sis.transfers import TransferError, transfer_student

        student = self.get_object()
        campus = Campus.objects.filter(
            tenant_id=request.tenant_id, id=request.data.get("to_campus")
        ).first()
        try:
            record = transfer_student(
                student,
                to_campus=campus,
                effective_on=request.data.get("effective_on") or None,
                reason=request.data.get("reason", ""),
                requested_by=_email(request),
            )
        except TransferError as exc:
            return Response({"detail": str(exc)}, status=409)

        write_audit(request, "update", student)
        return Response({
            "transfer": str(record.id),
            "student": str(student.id),
            "from_campus": str(record.from_campus_id) if record.from_campus_id else None,
            "to_campus": str(record.to_campus_id),
            "effective_on": record.effective_on,
            "enrolments_ended": record.enrolments_ended,
        }, status=201)

    @action(detail=True, methods=["get"], url_path="campus-history")
    def campus_history(self, request, pk=None):
        """Every campus this student has attended, and when they moved."""
        student = self.get_object()
        return Response({
            "student": str(student.id),
            "current_campus": str(student.campus_id) if student.campus_id else None,
            "transfers": [
                {
                    "id": str(t.id),
                    "from_campus": t.from_campus.name if t.from_campus else None,
                    "to_campus": t.to_campus.name,
                    "effective_on": t.effective_on,
                    "reason": t.reason,
                    "enrolments_ended": t.enrolments_ended,
                }
                for t in student.campus_transfers.select_related(
                    "from_campus", "to_campus"
                ).order_by("effective_on")
            ],
        })

    @action(detail=True, methods=["get"])
    def export(self, request, pk=None):
        """
        Data portability (ST4S / APP): the complete student record as JSON, for
        transfer to another school system.
        """
        student = self.get_object()
        tenant = student.tenant_id
        from products.cyed.attendance.models import AttendanceMark
        from products.cyed.fees.models import Invoice
        from products.cyed.gradebook.models import Grade
        from products.cyed.reporting.models import ReportCard
        from products.cyed.wellbeing.models import LearnerProfile

        record = {
            "student": StudentSerializer(student).data,
            "guardians": [
                {"name": f"{g.first_name} {g.last_name}", "relationship": g.relationship,
                 "email": g.email, "phone": g.phone}
                for g in student.guardians.all()
            ],
            "enrolments": list(
                Enrolment.objects.filter(tenant_id=tenant, student=student)
                .values("class_section__name", "status", "enrolled_on")
            ),
            "grades": list(
                Grade.objects.filter(tenant_id=tenant, student=student)
                .values("assessment__name", "score", "achievement_level")
            ),
            "attendance": list(
                AttendanceMark.objects.filter(tenant_id=tenant, student=student)
                .values("roll_call__date", "status")
            ),
            "invoices": list(
                Invoice.objects.filter(tenant_id=tenant, student=student)
                .values("description", "amount", "status")
            ),
            "report_cards": list(
                ReportCard.objects.filter(tenant_id=tenant, student=student)
                .values("term", "status")
            ),
            "learner_profile": (
                LearnerProfile.objects.filter(tenant_id=tenant, student=student)
                .values("eald_level", "is_neurodivergent", "accommodations").first()
            ),
        }
        write_audit(request, "read_sensitive", student)
        return Response(record)

    @action(detail=False, methods=["post"], url_path="import")
    def bulk_import(self, request):
        """
        Data-migration import: POST a CSV file (multipart field `file`) to
        create/update students in bulk. Staff-only; returns a per-row report.
        """
        upload = request.FILES.get("file")
        if upload is None:
            return Response({"detail": "Attach a CSV as form field 'file'."}, status=400)
        from products.cyed.sis.imports import import_students

        report = import_students(request.tenant_id, upload.read())
        return Response(report)

    @action(detail=True, methods=["post"])
    def deidentify(self, request, pk=None):
        """
        Right to erasure / de-identification (APP): permanently strip PII while
        preserving anonymised records for statistics. Irreversible.
        """
        student = self.get_object()
        student.first_name = "De-identified"
        student.last_name = f"Student {str(student.id)[:8]}"
        student.email = ""
        student.student_number = ""
        student.date_of_birth = None
        student.enrolment_status = "withdrawn"
        student.save()
        student.guardians.clear()
        write_audit(request, "update", student)
        return Response({"detail": "Student record de-identified.", "id": str(student.id)})


class ClassSectionViewSet(CampusScopedMixin, TenantScopedModelViewSet):
    queryset = ClassSection.objects.select_related("academic_year", "teacher").all()
    serializer_class = ClassSectionSerializer

    @action(detail=False, methods=["get"], url_path="mine")
    def mine(self, request):
        """
        The logged-in teacher's own classes — answers "what do I teach?"
        Requires the account's email to match an hr.Staff record and that
        Staff to be linked as `teacher` on the class (see sis migration 0004;
        classes never backfilled to a Staff record won't appear here even if
        they show a name in `teacher_name` — that's the point).
        """
        email = _email(request)
        if not email:
            return Response([])
        from products.cyed.hr.models import Staff

        staff = Staff.objects.filter(tenant_id=request.tenant_id, email__iexact=email).first()
        if not staff:
            return Response(
                {"detail": "No staff record linked to this account's email."}, status=404
            )
        qs = self.get_queryset().filter(teacher=staff)
        return Response(self.get_serializer(qs, many=True).data)


class EnrolmentViewSet(TenantScopedModelViewSet):
    queryset = Enrolment.objects.select_related("student", "class_section").all()
    serializer_class = EnrolmentSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        class_section = self.request.query_params.get("class_section")
        student = self.request.query_params.get("student")
        if class_section:
            qs = qs.filter(class_section_id=class_section)
        if student:
            qs = qs.filter(student_id=student)
        return qs
