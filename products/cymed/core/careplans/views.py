from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from products.cymed.core.careplans.models import CarePlan
from products.cymed.core.careplans.serializers import CarePlanSerializer

class CarePlanViewSet(viewsets.ModelViewSet):
    queryset = CarePlan.objects.all()
    serializer_class = CarePlanSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        tenant_id = getattr(self.request, "tenant_id", None)
        if tenant_id:
            return self.queryset.filter(tenant_id=tenant_id)
        return self.queryset.none()
