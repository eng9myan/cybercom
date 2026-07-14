from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import SystemAuditLog
from .serializers import SystemAuditLogSerializer

class SystemAuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = SystemAuditLogSerializer

    def get_queryset(self):
        # Enforce multi-tenancy access boundary
        return SystemAuditLog.objects.filter(
            tenant_id=self.request.tenant_id
        ).order_by('-timestamp')
