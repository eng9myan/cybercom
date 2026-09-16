from django.db.models import Count

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from core.viewsets import TenantScopedModelViewSet
from products.cyed.curriculum import mrac
from products.cyed.curriculum.importer import import_outcomes
from products.cyed.curriculum.models import (
    AchievementStandard,
    CrossCurriculumPriority,
    CurriculumOutcome,
    GeneralCapability,
    MracImportRun,
)
from products.cyed.curriculum.serializers import (
    AchievementStandardSerializer,
    CrossCurriculumPrioritySerializer,
    CurriculumOutcomeSerializer,
    GeneralCapabilitySerializer,
    MracImportRunSerializer,
)
from products.cyed.governance.access import IsStaff


class _StaffReadOnlyTenantViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Reference data owned by the ACARA import, not by users: list/retrieve only,
    staff only, always scoped to the caller's tenant.
    """

    permission_classes = [IsStaff]

    def get_queryset(self):
        qs = super().get_queryset()
        tenant_id = getattr(self.request, "tenant_id", None)
        if tenant_id is None:
            return qs
        return qs.filter(tenant_id=tenant_id)


class GeneralCapabilityViewSet(_StaffReadOnlyTenantViewSet):
    queryset = GeneralCapability.objects.all()
    serializer_class = GeneralCapabilitySerializer

    def get_queryset(self):
        qs = super().get_queryset()
        code = self.request.query_params.get("code")
        return qs.filter(code__iexact=code) if code else qs


class CrossCurriculumPriorityViewSet(_StaffReadOnlyTenantViewSet):
    queryset = CrossCurriculumPriority.objects.all()
    serializer_class = CrossCurriculumPrioritySerializer

    def get_queryset(self):
        qs = super().get_queryset()
        code = self.request.query_params.get("code")
        return qs.filter(code__iexact=code) if code else qs


class AchievementStandardViewSet(_StaffReadOnlyTenantViewSet):
    queryset = AchievementStandard.objects.all()
    serializer_class = AchievementStandardSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        params = self.request.query_params
        if params.get("learning_area"):
            qs = qs.filter(learning_area__iexact=params["learning_area"])
        if params.get("year_level"):
            qs = qs.filter(year_level=params["year_level"])
        return qs


class MracImportRunViewSet(_StaffReadOnlyTenantViewSet):
    """Audit trail of MRAC ingestion runs — each row carries the ACARA notice."""

    queryset = MracImportRun.objects.all()
    serializer_class = MracImportRunSerializer


class CurriculumOutcomeViewSet(TenantScopedModelViewSet):
    queryset = CurriculumOutcome.objects.all()
    serializer_class = CurriculumOutcomeSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        params = self.request.query_params
        learning_area = params.get("learning_area")
        year_level = params.get("year_level")
        code = params.get("code")
        framework = params.get("framework")
        capability = params.get("general_capability")
        priority = params.get("cross_curriculum_priority")
        elaborations = params.get("elaborations")
        parent = params.get("parent_code")

        if learning_area:
            qs = qs.filter(learning_area__iexact=learning_area)
        if year_level:
            qs = qs.filter(year_level=year_level)
        if code:
            qs = qs.filter(code__icontains=code)
        if framework:
            qs = qs.filter(framework=framework)
        if capability:
            qs = qs.filter(general_capabilities__code__iexact=capability)
        if priority:
            qs = qs.filter(cross_curriculum_priorities__code__iexact=priority)
        if parent:
            qs = qs.filter(parent_outcome__code__iexact=parent)
        if elaborations is not None:
            flag = str(elaborations).lower()
            if flag in ("0", "false", "no", "exclude"):
                qs = qs.filter(is_elaboration=False)
            elif flag in ("1", "true", "yes", "only"):
                qs = qs.filter(is_elaboration=True)
        return qs.distinct()

    # ── Ingestion ───────────────────────────────────────────────────────────
    @action(detail=False, methods=["post"], permission_classes=[IsStaff])
    def bulk_import(self, request):
        """
        Staff-only bulk ingestion of ACARA outcomes.
        Body: { "outcomes": [ {code, learning_area, year_level, ...}, ... ],
                "framework": "ACARA v9" }
        Idempotent (upsert by code+framework).
        """
        rows = request.data.get("outcomes")
        if not isinstance(rows, list):
            return Response({"detail": "'outcomes' must be a list."}, status=status.HTTP_400_BAD_REQUEST)
        framework = request.data.get("framework", "ACARA v9")
        result = import_outcomes(request.tenant_id, rows, framework=framework)
        return Response(result, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"], url_path="import-mrac", permission_classes=[IsStaff])
    def import_mrac(self, request):
        """
        Staff-only ingestion of a MRAC (Machine-Readable Australian Curriculum)
        JSON-LD document supplied inline — no filesystem or network access.

        Body: { "document": <the parsed JSON-LD>, "set_code": "LA/MAT",
                "framework": "ACARA v9" }
        Idempotent: re-posting the same document updates, never duplicates.
        """
        document = request.data.get("document")
        if document is None:
            return Response(
                {"detail": "'document' (the MRAC JSON-LD) is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            result = mrac.load_mrac(
                request.tenant_id,
                document,
                set_code=request.data.get("set_code"),
                framework=request.data.get("framework", "ACARA v9"),
            )
        except mrac.MracParseError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(result, status=status.HTTP_200_OK)

    # ── Coverage / stats ────────────────────────────────────────────────────
    @action(detail=False, methods=["get"], permission_classes=[IsStaff])
    def coverage(self, request):
        """
        How much of the Australian Curriculum this tenant actually holds —
        outcome counts per learning area and per year level. This is the
        evidence a school needs that ACARA coverage is real, not seeded.

        Query params: ?framework=  ?include_elaborations=false
        """
        qs = CurriculumOutcome.objects.filter(tenant_id=request.tenant_id)
        framework = request.query_params.get("framework")
        if framework:
            qs = qs.filter(framework=framework)
        include = str(request.query_params.get("include_elaborations", "true")).lower()
        if include in ("0", "false", "no"):
            qs = qs.filter(is_elaboration=False)

        by_area = list(
            qs.values("learning_area").annotate(count=Count("id")).order_by("learning_area")
        )
        by_year = list(qs.values("year_level").annotate(count=Count("id")).order_by("year_level"))
        by_area_year = list(
            qs.values("learning_area", "year_level")
            .annotate(count=Count("id"))
            .order_by("learning_area", "year_level")
        )

        total = qs.count()
        elaborations = qs.filter(is_elaboration=True).count()
        return Response(
            {
                "framework": framework or "all",
                "total_outcomes": total,
                "content_descriptions": total - elaborations,
                "elaborations": elaborations,
                "learning_areas": len(by_area),
                "year_levels": len(by_year),
                "by_learning_area": by_area,
                "by_year_level": by_year,
                "by_learning_area_and_year": by_area_year,
                "general_capabilities": GeneralCapability.objects.filter(
                    tenant_id=request.tenant_id
                ).count(),
                "cross_curriculum_priorities": CrossCurriculumPriority.objects.filter(
                    tenant_id=request.tenant_id
                ).count(),
                "achievement_standards": AchievementStandard.objects.filter(
                    tenant_id=request.tenant_id
                ).count(),
                "outcomes_linked_to_standard": qs.exclude(achievement_standard_ref=None).count(),
                "import_runs": MracImportRun.objects.filter(tenant_id=request.tenant_id).count(),
                "attribution": mrac.ACARA_ATTRIBUTION,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["get"])
    def elaborations(self, request, pk=None):
        """The elaborations hanging off one content description."""
        outcome = self.get_object()
        rows = outcome.elaborations.all().order_by("code")
        return Response(
            {
                "code": outcome.code,
                "count": rows.count(),
                "results": CurriculumOutcomeSerializer(rows, many=True, context={"request": request}).data,
            }
        )
