from django.utils import timezone
from rest_framework.decorators import action
from rest_framework.response import Response

from core.viewsets import TenantScopedModelViewSet
from products.cyed.governance.access import IsStaff
from products.cyed.visitors.models import Visitor
from products.cyed.visitors.serializers import VisitorSerializer


class VisitorViewSet(TenantScopedModelViewSet):
    queryset = Visitor.objects.all()
    serializer_class = VisitorSerializer
    permission_classes = [IsStaff]

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.query_params.get("on_site") in ("1", "true", "True"):
            qs = qs.filter(signed_in_at__isnull=False, signed_out_at__isnull=True)
        return qs

    def perform_create(self, serializer):
        serializer.save(tenant_id=self.request.tenant_id, signed_in_at=timezone.now())

    @action(detail=True, methods=["post"])
    def sign_out(self, request, pk=None):
        v = self.get_object()
        v.signed_out_at = timezone.now()
        v.save(update_fields=["signed_out_at", "updated_at"])
        return Response(self.get_serializer(v).data)
