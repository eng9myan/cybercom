from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import IsAuthenticatedViaClaims
from core.viewsets import TenantScopedModelViewSet
from platform.provisioning.models import (
    CompanyBlueprint,
    CountryPack,
    DepartmentPack,
    IndustryTemplate,
    TenantConfigParameter,
)
from platform.provisioning.serializers import (
    CompanyBlueprintSerializer,
    CountryPackSerializer,
    DepartmentPackSerializer,
    IndustryTemplateSerializer,
    TenantConfigParameterSerializer,
)
from platform.provisioning.proposal import propose
from platform.provisioning.services import ProvisioningError, ProvisioningService


# -- Catalog (global reference data; read-only to tenants) ------------------


class CountryPackViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticatedViaClaims]
    serializer_class = CountryPackSerializer
    queryset = CountryPack.objects.filter(is_active=True)
    lookup_field = "code"


class DepartmentPackViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticatedViaClaims]
    serializer_class = DepartmentPackSerializer
    queryset = DepartmentPack.objects.filter(is_active=True)
    lookup_field = "key"


class IndustryTemplateViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticatedViaClaims]
    serializer_class = IndustryTemplateSerializer
    queryset = IndustryTemplate.objects.filter(is_active=True)
    lookup_field = "key"


# -- Blueprint (tenant-scoped: the wizard's persisted answers) --------------


class CompanyBlueprintViewSet(TenantScopedModelViewSet):
    serializer_class = CompanyBlueprintSerializer
    queryset = CompanyBlueprint.objects.all()

    @action(detail=True, methods=["post"])
    def provision(self, request, pk=None):
        """Run ProvisioningService — 'Create My Company'. Idempotent."""
        blueprint = self.get_object()
        try:
            result = ProvisioningService(blueprint).build()
        except ProvisioningError as exc:
            blueprint.status = "failed"
            blueprint.save(update_fields=["status", "updated_at"])
            return Response({"detail": str(exc)}, status=400)
        return Response(CompanyBlueprintSerializer(result).data, status=200)

    @action(detail=True, methods=["get"])
    def upgrade_preview(self, request, pk=None):
        """
        Template versioning: show what changed between the version this
        company was provisioned with and the latest active version. The
        customer previews before opting in; re-running `provision` applies
        (get_or_create semantics protect existing customizations — nothing
        is deleted or overwritten, only missing pieces are added).
        """
        blueprint = self.get_object()
        latest = (
            IndustryTemplate.objects.filter(key=blueprint.industry_key, is_active=True)
            .order_by("-version")
            .first()
        )
        if not latest:
            return Response({"detail": "No active template for this industry."}, status=404)
        used = blueprint.template_version_used or "—"
        if used == latest.version:
            return Response({"up_to_date": True, "current_version": used})

        old = IndustryTemplate.objects.filter(
            key=blueprint.industry_key, version=used
        ).first()

        def diff(field: str):
            new_val = getattr(latest, field) or []
            old_val = (getattr(old, field) if old else None) or []
            if isinstance(new_val, list) and all(isinstance(x, str) for x in new_val):
                return sorted(set(new_val) - set(old_val))
            return new_val if new_val != old_val else []

        return Response({
            "up_to_date": False,
            "current_version": used,
            "latest_version": latest.version,
            "added_department_packs": diff("department_pack_keys"),
            "changed_approval_matrix": diff("approval_matrix"),
            "added_reports": diff("reports"),
            "added_dashboards": diff("dashboards"),
            "added_import_templates": diff("import_templates"),
            "how_to_apply": "POST /provision again — additive only; your customizations are preserved.",
        })


class TenantConfigParameterViewSet(TenantScopedModelViewSet):
    """Tenant KV store backing the legacy ir.config_parameter calls."""

    serializer_class = TenantConfigParameterSerializer
    queryset = TenantConfigParameter.objects.all()
    filterset_fields = ["key"]

    @action(detail=False, methods=["post"])
    def set(self, request):
        key = (request.data.get("key") or "").strip()
        if not key:
            return Response({"detail": "key is required."}, status=400)
        obj, _ = TenantConfigParameter.objects.update_or_create(
            tenant_id=request.tenant_id,
            key=key,
            defaults={"value": str(request.data.get("value") or "")},
        )
        return Response(TenantConfigParameterSerializer(obj).data)

    @action(detail=False, methods=["get"])
    def get(self, request):
        key = (request.query_params.get("key") or "").strip()
        obj = self.get_queryset().filter(key=key).first()
        return Response({"key": key, "value": obj.value if obj else None})


class AIProposalView(APIView):
    """
    AI-guided configuration: POST {"description": "..."} with a plain-language
    company description → proposed industry template + department packs, with
    evidence and rationale for the customer to review before creating.
    """

    permission_classes = [IsAuthenticatedViaClaims]

    def post(self, request):
        description = (request.data.get("description") or "").strip()
        if len(description) < 10:
            return Response(
                {"detail": "Describe the company in a sentence or two (at least 10 characters)."},
                status=400,
            )
        return Response(propose(description))
