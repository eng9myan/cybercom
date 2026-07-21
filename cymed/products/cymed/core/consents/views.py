from django.db.models import Q
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from products.cymed.core.consents.models import Consent
from products.cymed.core.consents.serializers import ConsentSerializer


class ConsentViewSet(viewsets.ModelViewSet):
    queryset = Consent.objects.all()
    serializer_class = ConsentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        tenant_id = getattr(self.request, "tenant_id", None)
        if not tenant_id:
            return self.queryset.none()
        # CyID ecosystem, Phase 4 — a tenant sees consents it owns AND
        # consents explicitly granted to it (granted_to_tenant_id), e.g.
        # a pharmacy reading a consent a clinic created and shared with it.
        return self.queryset.filter(Q(tenant_id=tenant_id) | Q(granted_to_tenant_id=tenant_id))
