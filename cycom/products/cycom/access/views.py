from rest_framework.decorators import action
from rest_framework.response import Response

from core.viewsets import TenantScopedModelViewSet
from platform.tenant.permissions import IsPlatformAdmin
from products.cycom.access.credentials import set_manager_barcode, set_manager_pin
from products.cycom.access.models import AccessGrant, Role, RoleAssignment
from products.cycom.access.serializers import (
    AccessGrantSerializer,
    RoleAssignmentSerializer,
    RoleSerializer,
)
from products.cycom.access.services import create_grant, resolve_pending_invites

# Granting/revoking access is itself a privileged action — every viewset
# here is platform-admin-only, unlike the rest of Cycom's tenant-scoped
# read/write endpoints.


class RoleViewSet(TenantScopedModelViewSet):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [IsPlatformAdmin]


class RoleAssignmentViewSet(TenantScopedModelViewSet):
    queryset = RoleAssignment.objects.select_related("role").all()
    serializer_class = RoleAssignmentSerializer
    permission_classes = [IsPlatformAdmin]

    def get_queryset(self):
        # The Team page is the first authenticated request a just-invited
        # user's session makes — resolve any "pending:<their email>"
        # placeholder to their real sub before listing, so they see their
        # own assignment land immediately instead of needing a second visit.
        claims = getattr(self.request, "auth_claims", {}) or {}
        tenant_id = getattr(self.request, "tenant_id", None)
        if tenant_id is not None:
            resolve_pending_invites(tenant_id, claims.get("sub"), claims.get("email"))
        return super().get_queryset()

    @action(detail=True, methods=["post"], url_path="set-manager-pin")
    def set_manager_pin_action(self, request, pk=None):
        """Sets/rotates this role assignment's till PIN — admin-only (matches
        every other write on this viewset). Never returns the PIN back."""
        assignment = self.get_object()
        set_manager_pin(assignment, request.data.get("pin"))
        return Response({"detail": "PIN set."})

    @action(detail=True, methods=["post"], url_path="set-manager-barcode")
    def set_manager_barcode_action(self, request, pk=None):
        assignment = self.get_object()
        set_manager_barcode(assignment, request.data.get("barcode"))
        return Response({"detail": "Barcode set."})


class AccessGrantViewSet(TenantScopedModelViewSet):
    queryset = AccessGrant.objects.select_related("role", "warehouse", "product").all()
    serializer_class = AccessGrantSerializer
    permission_classes = [IsPlatformAdmin]

    def create(self, request, *args, **kwargs):
        grant = create_grant(
            tenant_id=request.tenant_id,
            subject_type=request.data.get("subject_type"),
            user_id=request.data.get("user_id", ""),
            role_id=request.data.get("role"),
            warehouse_id=request.data.get("warehouse"),
            product_id=request.data.get("product"),
        )
        return Response(AccessGrantSerializer(grant).data, status=201)
