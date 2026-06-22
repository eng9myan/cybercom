from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from products.cymed.core.facilities.models import Facility
from products.cymed.core.facilities.serializers import FacilitySerializer

class FacilityViewSet(viewsets.ModelViewSet):
    queryset = Facility.objects.filter(is_active=True)
    serializer_class = FacilitySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        tenant_id = getattr(self.request, "tenant_id", None)
        if tenant_id:
            return self.queryset.filter(tenant_id=tenant_id)
        return self.queryset.none()
