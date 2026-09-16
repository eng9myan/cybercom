from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from core.viewsets import TenantScopedModelViewSet
from products.cyed.admissions import enrolment as enrolment_service
from products.cyed.admissions.models import (
    Application,
    ApplicationDocument,
    CatchmentZone,
    Offer,
)
from products.cyed.admissions.serializers import (
    ApplicationDocumentSerializer,
    ApplicationSerializer,
    CatchmentZoneSerializer,
    OfferSerializer,
)
from products.cyed.governance.access import _email


class CatchmentZoneViewSet(TenantScopedModelViewSet):
    queryset = CatchmentZone.objects.select_related("campus").all()
    serializer_class = CatchmentZoneSerializer

    @action(detail=False, methods=["get"])
    def check(self, request):
        """
        Is an address in zone? `?suburb=Richmond&postcode=3121&campus=<uuid>`.

        A verdict, not a gate: out of zone is a fact a registrar weighs, and
        most schools can enrol out of zone when there is room.
        """
        return Response(enrolment_service.catchment_check(
            request.tenant_id,
            suburb=request.query_params.get("suburb", ""),
            postcode=request.query_params.get("postcode", ""),
            campus_id=request.query_params.get("campus"),
        ))


class ApplicationDocumentViewSet(TenantScopedModelViewSet):
    queryset = ApplicationDocument.objects.select_related("application").all()
    serializer_class = ApplicationDocumentSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        params = self.request.query_params
        if params.get("application"):
            qs = qs.filter(application_id=params["application"])
        if params.get("outstanding") == "1":
            qs = qs.filter(is_received=False)
        return qs

    @action(detail=True, methods=["post"], url_path="receive")
    def receive(self, request, pk=None):
        """Mark a document as sighted, recording who sighted it and when."""
        document = self.get_object()
        document.is_received = True
        document.received_on = timezone.localdate()
        document.received_by = _email(request)
        document.document_ref = request.data.get("document_ref", document.document_ref)
        document.save(update_fields=[
            "is_received", "received_on", "received_by", "document_ref", "updated_at",
        ])
        return Response(self.get_serializer(document).data)


class ApplicationViewSet(TenantScopedModelViewSet):
    queryset = Application.objects.prefetch_related("offers", "documents").all()
    serializer_class = ApplicationSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        params = self.request.query_params
        if params.get("status"):
            qs = qs.filter(status=params["status"])
        if params.get("year_level"):
            qs = qs.filter(year_level_applying=params["year_level"])
        if params.get("campus"):
            qs = qs.filter(campus_id=params["campus"])
        return qs

    @action(detail=True, methods=["get"])
    def catchment(self, request, pk=None):
        """Which zone this applicant's address falls into, if any."""
        return Response(
            enrolment_service.check_application_catchment(self.get_object())
        )

    @action(detail=True, methods=["post"], url_path="document-checklist")
    def document_checklist(self, request, pk=None):
        """Create the standard admissions checklist. Idempotent."""
        application = self.get_object()
        created = enrolment_service.ensure_document_checklist(application)
        return Response({
            "application": str(application.id),
            "created": len(created),
            "documents": ApplicationDocumentSerializer(
                application.documents.all(), many=True
            ).data,
        })

    @action(detail=True, methods=["post"], url_path="waitlist")
    def add_waitlist(self, request, pk=None):
        """Put this application in the queue for its year level."""
        application = self.get_object()
        rank = request.data.get("rank")
        enrolment_service.add_to_waitlist(
            application, rank=int(rank) if rank is not None else None
        )
        return Response(self.get_serializer(application).data)

    @action(detail=False, methods=["get"], url_path="waitlist")
    def waitlist(self, request):
        """The queue, in rank order."""
        year_level = request.query_params.get("year_level")
        qs = enrolment_service.waitlist(
            request.tenant_id,
            year_level=int(year_level) if year_level else None,
            campus_id=request.query_params.get("campus"),
        )
        return Response({
            "count": qs.count(),
            "results": [
                {
                    "application": str(a.id),
                    "name": a.applicant_name(),
                    "year_level": a.year_level_applying,
                    "rank": a.waitlist_rank,
                    "applied_on": a.created_at.date().isoformat(),
                }
                for a in qs
            ],
        })

    @action(detail=True, methods=["post"])
    def enrol(self, request, pk=None):
        """
        Convert an accepted application into a fully set-up student.

        Beyond creating the Student this attaches the guardian, joins or opens
        the household, raises the fee schedule with any sibling discount
        applied, allocates a class, and opens an immunisation record. The
        response names everything created *and everything skipped* — the
        outstanding list is the half a registrar needs.

        Body (all optional): ``{"fee_plan": uuid, "class_section": uuid,
        "family": uuid, "academic_year": uuid, "campus": uuid,
        "require_documents": true}``
        """
        from products.cyed.billing.models import FeePlan
        from products.cyed.org.models import Campus
        from products.cyed.sis.models import AcademicYear, ClassSection, Family

        application = self.get_object()
        tenant = request.tenant_id

        def _lookup(model, key):
            value = request.data.get(key)
            if not value:
                return None, None
            obj = model.objects.filter(tenant_id=tenant, id=value).first()
            if obj is None:
                return None, f"No {model.__name__} with id {value} in this school."
            return obj, None

        resolved = {}
        for key, model in (
            ("fee_plan", FeePlan), ("class_section", ClassSection), ("family", Family),
            ("academic_year", AcademicYear), ("campus", Campus),
        ):
            obj, problem = _lookup(model, key)
            if problem:
                return Response({"detail": problem}, status=status.HTTP_400_BAD_REQUEST)
            resolved[key] = obj

        try:
            student, report = enrolment_service.enrol_application(
                application,
                fee_plan=resolved["fee_plan"],
                class_section=resolved["class_section"],
                family=resolved["family"],
                academic_year=resolved["academic_year"],
                campus=resolved["campus"],
                require_documents=bool(request.data.get("require_documents", True)),
                actor=_email(request),
            )
        except enrolment_service.AdmissionsError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_409_CONFLICT)

        return Response(
            {"student_id": str(student.id), "status": application.status, **report},
            status=status.HTTP_201_CREATED,
        )


class OfferViewSet(TenantScopedModelViewSet):
    queryset = Offer.objects.select_related("application").all()
    serializer_class = OfferSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        params = self.request.query_params
        if params.get("application"):
            qs = qs.filter(application_id=params["application"])
        if params.get("response"):
            qs = qs.filter(response=params["response"])
        return qs

    def _respond(self, request, response):
        offer = self.get_object()
        try:
            enrolment_service.respond_to_offer(
                offer,
                response=response,
                responded_by=_email(request) or request.data.get("responded_by", ""),
                decline_reason=request.data.get("reason", ""),
            )
        except enrolment_service.AdmissionsError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_409_CONFLICT)
        return Response(self.get_serializer(offer).data)

    @action(detail=True, methods=["post"])
    def accept(self, request, pk=None):
        """The family accepts the place."""
        return self._respond(request, "accepted")

    @action(detail=True, methods=["post"])
    def decline(self, request, pk=None):
        """The family turns the place down."""
        return self._respond(request, "declined")

    @action(detail=False, methods=["post"], url_path="lapse-expired")
    def lapse_expired(self, request):
        """
        Close out offers nobody answered by their expiry date.

        Run daily. Without it an unanswered offer holds a place open forever
        and the waitlist behind it never moves — a failure that looks like
        nothing is wrong.
        """
        lapsed = enrolment_service.lapse_expired_offers(request.tenant_id)
        return Response({
            "lapsed": len(lapsed),
            "offers": [str(o.id) for o in lapsed],
        })
