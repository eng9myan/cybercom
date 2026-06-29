"""
CyMed Laboratory — Base ViewSet
Tenant isolation + feature flag gating for all laboratory endpoints.
"""

from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated


class LaboratoryModelViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    required_feature: str = ""

    def get_queryset(self):
        tenant_id = getattr(self.request, "tenant_id", None)
        if tenant_id:
            return self.queryset.filter(tenant_id=tenant_id)
        return self.queryset.none()

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        if self.required_feature:
            self._check_feature(request, self.required_feature)

    def _check_feature(self, request, feature_code: str) -> None:
        from products.cymed.commercial.feature_flags.services import FeatureFlagService

        tenant_id = getattr(request, "tenant_id", None)
        if not FeatureFlagService.is_enabled(
            feature_code, tenant_id=str(tenant_id) if tenant_id else None
        ):
            raise PermissionDenied(
                detail=f"Feature '{feature_code}' is not enabled for your laboratory edition."
            )

    def perform_create(self, serializer):
        tenant_id = getattr(self.request, "tenant_id", None)
        serializer.save(tenant_id=tenant_id)
