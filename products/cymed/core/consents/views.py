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
        if tenant_id:
            return self.queryset.filter(tenant_id=tenant_id)
        return self.queryset.none()
