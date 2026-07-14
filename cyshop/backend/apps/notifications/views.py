from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import SystemNotification
from .serializers import SystemNotificationSerializer

class SystemNotificationViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = SystemNotificationSerializer

    def get_queryset(self):
        # Enforce multi-tenancy and return notifications belonging only to the authenticated user
        return SystemNotification.objects.filter(
            tenant_id=self.request.tenant_id,
            user=self.request.user,
            is_deleted=False
        ).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(
            user=self.request.user,
            tenant_id=self.request.tenant_id
        )
