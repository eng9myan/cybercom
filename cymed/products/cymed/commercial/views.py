from rest_framework import viewsets
from platform.api.permissions import StaffReadPlatformAdminWrite
from platform.api.tenancy import PLATFORM_TENANT_ID


class CommercialModelViewSet(viewsets.ModelViewSet):
    """
    Base ViewSet for all CyMed Commercial module endpoints.

    Commercial data is vendor-side. Catalog rows (editions, flags, profiles,
    product versions) are seeded under PLATFORM_TENANT_ID and every tenant may
    read them; per-customer rows (licences, subscriptions …) are visible to the
    tenant they belong to. Tenant scoping itself comes from the project-wide
    TenantScopeFilterBackend / TenantObjectGuardMiddleware (platform.api.tenancy).

    Writes are platform_admin only. Previously any authenticated staff member
    could POST a licence or subscription for their own tenant — i.e. grant
    themselves paid features — or edit the shared catalog.
    """

    permission_classes = [StaffReadPlatformAdminWrite]
    shared_tenant_ids = (PLATFORM_TENANT_ID,)

    def perform_create(self, serializer):
        """Inject tenant_id from JWT into new records where applicable."""
        tenant_id = getattr(self.request, "tenant_id", None)
        if tenant_id and hasattr(serializer.Meta.model, "tenant_id"):
            serializer.save(tenant_id=tenant_id)
        else:
            serializer.save()
