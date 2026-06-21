from rest_framework import generics, permissions
from .models import Tenant
from .serializers import TenantSerializer


class TenantListView(generics.ListAPIView):
    """List all active tenants. Platform admin only."""
    queryset = Tenant.objects.filter(status="active")
    serializer_class = TenantSerializer
    permission_classes = [permissions.IsAdminUser]


class TenantDetailView(generics.RetrieveAPIView):
    """Retrieve a single tenant by PK."""
    queryset = Tenant.objects.all()
    serializer_class = TenantSerializer
    permission_classes = [permissions.IsAdminUser]
