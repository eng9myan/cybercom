from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import BasePermission
from rest_framework.response import Response

from platform.api.tenancy import is_platform_admin
from products.cymed.commercial.editions.models import (
    EditionFeature,
    EditionLimit,
    EditionModule,
    ProductCatalogEntry,
    ProductEdition,
    TenantProductSubscription,
)
from products.cymed.commercial.editions.serializers import (
    EditionFeatureSerializer,
    EditionLimitSerializer,
    EditionModuleSerializer,
    ProductCatalogEntrySerializer,
    ProductEditionSerializer,
    TenantProductSubscriptionSerializer,
)
from products.cymed.commercial.editions.services import EditionService
from products.cymed.commercial.views import CommercialModelViewSet


class ProductCatalogEntryViewSet(CommercialModelViewSet):
    queryset = ProductCatalogEntry.objects.all()
    serializer_class = ProductCatalogEntrySerializer


class ProductEditionViewSet(CommercialModelViewSet):
    queryset = ProductEdition.objects.select_related("product").prefetch_related(
        "features", "limits", "modules"
    )
    serializer_class = ProductEditionSerializer

    @action(detail=True, methods=["get"])
    def feature_matrix(self, request, pk=None):
        """Return the full feature matrix for this edition."""
        edition = self.get_object()
        features = EditionFeature.objects.filter(edition=edition)
        return Response(
            {
                "edition": edition.code,
                "product": edition.product.code,
                "features": EditionFeatureSerializer(features, many=True).data,
            }
        )


class EditionFeatureViewSet(CommercialModelViewSet):
    queryset = EditionFeature.objects.all()
    serializer_class = EditionFeatureSerializer


class EditionLimitViewSet(CommercialModelViewSet):
    queryset = EditionLimit.objects.all()
    serializer_class = EditionLimitSerializer


class EditionModuleViewSet(CommercialModelViewSet):
    queryset = EditionModule.objects.all()
    serializer_class = EditionModuleSerializer


class IsPlatformAdminOnly(BasePermission):
    """Granting a tenant a product subscription is a vendor-side action
    across every tenant — only platform_admin, not even tenant_admin, may
    call this."""

    message = "Only a platform administrator may manage product subscriptions."

    def has_permission(self, request, view):
        return is_platform_admin(request)


class TenantProductSubscriptionViewSet(viewsets.ModelViewSet):
    """
    Admin console for granting a tenant access to a CyMed product (hospital/
    clinic/pharmacy/laboratory/imaging) — the provisioning UI flagged as
    missing after Phase 1 entitlement gating shipped with no way to actually
    create these rows outside the Django admin/shell.

    Deliberately not a CommercialModelViewSet: that base's perform_create
    overwrites the row's tenant_id with the CALLER's own request.tenant_id,
    which is right for a tenant managing its own licence but wrong here —
    granting is inherently cross-tenant (the target tenant is whoever the
    admin names in the payload, never the admin's own tenant).
    tenant_scope_exempt so this also works regardless of whatever
    X-Tenant-ID header a given admin console deployment happens to send.
    """

    permission_classes = [IsPlatformAdminOnly]
    tenant_scope_exempt = True
    serializer_class = TenantProductSubscriptionSerializer
    queryset = TenantProductSubscription.objects.select_related("product", "edition").all()

    @action(detail=False, methods=["post"])
    def grant(self, request):
        """Create or change the one subscription row a tenant may have per
        product (unique_together tenant_id+product) — grant/upgrade/downgrade
        in a single idempotent call instead of making the caller find-then-PATCH."""
        tenant_id = request.data.get("tenant_id")
        product_code = request.data.get("product_code")
        edition_code = request.data.get("edition_code")
        if not (tenant_id and product_code and edition_code):
            return Response(
                {"detail": "tenant_id, product_code and edition_code are required."},
                status=400,
            )
        edition = EditionService.get_edition(product_code, edition_code)
        if not edition:
            return Response({"detail": "Unknown product/edition."}, status=404)
        sub, _ = TenantProductSubscription.objects.update_or_create(
            tenant_id=tenant_id,
            product=edition.product,
            defaults={"edition": edition, "is_active": True},
        )
        return Response(TenantProductSubscriptionSerializer(sub).data, status=200)
