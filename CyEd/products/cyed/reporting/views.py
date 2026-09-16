from django.db.models import Max
from django.http import Http404, HttpResponse
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from core.permissions import IsAuthenticatedViaClaims
from core.viewsets import TenantScopedModelViewSet
from products.cyed.governance.access import IsStaff, is_staff, scope_queryset_by_student, visible_student_ids
from products.cyed.reporting.documents import build_snapshot, content_hash, render_report_pdf
from products.cyed.reporting.models import ReportCard, ReportCardDocument, ReportCardEntry
from products.cyed.reporting.serializers import (
    ReportCardDocumentSerializer,
    ReportCardEntrySerializer,
    ReportCardSerializer,
)


def _actor(request):
    return (getattr(request, "user_session", {}) or {}).get("email", "")


class ReportCardViewSet(TenantScopedModelViewSet):
    queryset = ReportCard.objects.select_related("student", "academic_year").prefetch_related("entries").all()
    serializer_class = ReportCardSerializer

    def get_permissions(self):
        # Families may view/download/acknowledge their child's report; only staff
        # may create, edit, or publish it.
        if self.action in ("list", "retrieve", "document", "pdf", "acknowledge"):
            return [IsAuthenticatedViaClaims()]
        return [IsStaff()]

    def get_queryset(self):
        qs = super().get_queryset()
        qs = scope_queryset_by_student(self.request, self.request.tenant_id, qs, student_path="student_id")
        student = self.request.query_params.get("student")
        status_filter = self.request.query_params.get("status")
        if student:
            qs = qs.filter(student_id=student)
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs

    def _latest_doc(self, report_card):
        return report_card.documents.order_by("-version").first()

    def _publish_one(self, report_card, actor, profile=None):
        """
        Publish → freeze snapshot, hash, render an immutable PDF as a new version.

        `profile` is passed in by the bulk path so the school branding and logo
        are fetched once per class rather than once per child.
        """
        report_card.publish()

        snapshot = build_snapshot(report_card)
        chash = content_hash(snapshot)
        next_version = (report_card.documents.aggregate(m=Max("version"))["m"] or 0) + 1

        if profile is None:
            from products.cyed.school.models import get_profile

            profile = get_profile(report_card.tenant_id)
        logo = bytes(profile.logo_bytes) if (profile.has_logo and profile.logo_content_type == "image/jpeg") else None
        pdf = render_report_pdf(snapshot, chash, next_version, logo_jpeg=logo)
        return ReportCardDocument.objects.create(
            tenant_id=report_card.tenant_id,
            report_card=report_card,
            version=next_version,
            content_hash=chash,
            snapshot=snapshot,
            pdf_bytes=pdf,
            published_by=actor,
        )

    @action(detail=True, methods=["post"])
    def publish(self, request, pk=None):
        """Publish one report card."""
        report_card = self.get_object()
        doc = self._publish_one(report_card, _actor(request))
        data = self.get_serializer(report_card).data
        data["document"] = {"version": doc.version, "content_hash": doc.content_hash, "verified": doc.verify()}
        return Response(data)

    @action(detail=False, methods=["post"], url_path="publish-class")
    def publish_class(self, request):
        """
        Publish every report card for a class section in one request.

        Body: ``{"class_section": "<uuid>", "term": "Semester 1",
        "academic_year": "<uuid>", "include_published": false}``

        A Year 7 teacher publishing thirty reports one at a time is the kind of
        friction that gets reporting done late. Only *draft* cards are published
        by default — re-publishing an already-issued report mints a new version
        of a document families may have downloaded, so it has to be asked for
        explicitly.

        Each card is published independently: one student with malformed
        entries does not block the other twenty-nine, and the failures come
        back named so they can be fixed.
        """
        class_section = request.data.get("class_section")
        if not class_section:
            return Response({"detail": "class_section is required."}, status=status.HTTP_400_BAD_REQUEST)

        from products.cyed.sis.models import Enrolment

        student_ids = list(
            Enrolment.objects.filter(
                tenant_id=request.tenant_id, class_section_id=class_section, status="active"
            ).values_list("student_id", flat=True)
        )
        if not student_ids:
            return Response(
                {"detail": "No students are actively enrolled in this class section."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        cards = ReportCard.objects.filter(
            tenant_id=request.tenant_id, student_id__in=student_ids
        ).select_related("student")
        if request.data.get("term"):
            cards = cards.filter(term=request.data["term"])
        if request.data.get("academic_year"):
            cards = cards.filter(academic_year_id=request.data["academic_year"])
        if not request.data.get("include_published"):
            cards = cards.filter(status="draft")

        from products.cyed.school.models import get_profile

        profile = get_profile(request.tenant_id)
        actor = _actor(request)

        published, failed = [], []
        for card in cards:
            try:
                doc = self._publish_one(card, actor, profile=profile)
            except Exception as exc:  # noqa: BLE001 — reported per student, not swallowed
                failed.append({
                    "report_card": str(card.id),
                    "student": str(card.student_id),
                    "name": f"{card.student.first_name} {card.student.last_name}".strip(),
                    "error": str(exc)[:255],
                })
                continue
            published.append({
                "report_card": str(card.id),
                "student": str(card.student_id),
                "name": f"{card.student.first_name} {card.student.last_name}".strip(),
                "version": doc.version,
                "content_hash": doc.content_hash,
            })

        return Response({
            "class_section": str(class_section),
            "roster": len(student_ids),
            "published": len(published),
            "failed": len(failed),
            # A student on the roster with no matching report card is not an
            # error, but a teacher needs to see the number to know whether the
            # whole class actually went out.
            "without_report_card": max(0, len(student_ids) - len(published) - len(failed)),
            "results": published,
            "failures": failed,
        })

    @action(detail=True, methods=["get"])
    def document(self, request, pk=None):
        doc = self._latest_doc(self.get_object())
        if doc is None:
            raise Http404("This report card has not been published yet.")
        return Response(ReportCardDocumentSerializer(doc).data)

    @action(detail=True, methods=["get"])
    def pdf(self, request, pk=None):
        doc = self._latest_doc(self.get_object())
        if doc is None:
            raise Http404("This report card has not been published yet.")
        resp = HttpResponse(bytes(doc.pdf_bytes), content_type="application/pdf")
        resp["Content-Disposition"] = f'inline; filename="report-{pk}-v{doc.version}.pdf"'
        return resp

    @action(detail=True, methods=["post"])
    def acknowledge(self, request, pk=None):
        """Parent (or staff) sign-off that they received the report."""
        report_card = self.get_object()
        if not is_staff(request):
            visible = visible_student_ids(request, request.tenant_id)
            if visible is not None and report_card.student_id not in visible:
                return Response({"detail": "Not permitted."}, status=status.HTTP_403_FORBIDDEN)
        doc = self._latest_doc(report_card)
        if doc is None:
            raise Http404("This report card has not been published yet.")
        doc.acknowledged_by = _actor(request)
        doc.acknowledged_at = timezone.now()
        doc.save(update_fields=["acknowledged_by", "acknowledged_at", "updated_at"])
        return Response(ReportCardDocumentSerializer(doc).data)


class ReportCardEntryViewSet(TenantScopedModelViewSet):
    queryset = ReportCardEntry.objects.select_related("report_card").all()
    serializer_class = ReportCardEntrySerializer
    permission_classes = [IsStaff]

    def get_queryset(self):
        qs = super().get_queryset()
        report_card = self.request.query_params.get("report_card")
        if report_card:
            qs = qs.filter(report_card_id=report_card)
        return qs
