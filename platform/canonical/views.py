from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from platform.canonical import flavors
from platform.canonical.models import VerticalFlavor
from platform.canonical.serializers import VerticalFlavorSerializer
from platform.tenant.permissions import IsPlatformAdmin


class VerticalFlavorViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only catalog of registered vertical flavors (blueprint N).

    The catalog itself is edited by changing flavor-registry.yaml or a
    *.flavor.yaml pack and re-syncing — either the `load_flavor_registry`
    management command on deploy, or `POST .../flavors/sync/` (admin-only)
    for an on-demand refresh without a redeploy.
    """

    queryset = VerticalFlavor.objects.all()
    serializer_class = VerticalFlavorSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "key"
    filterset_fields = ["status"]

    @action(detail=False, methods=["post"], permission_classes=[IsPlatformAdmin])
    def sync(self, request):
        registry_result = flavors.sync_registry()
        try:
            pack_result = flavors.sync_packs()
        except flavors.FlavorValidationError as exc:
            return Response(
                {"detail": str(exc), "registry": registry_result}, status=422
            )
        return Response({"registry": registry_result, "packs": pack_result})
