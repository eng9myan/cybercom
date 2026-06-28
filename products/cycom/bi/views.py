from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import BIReport, DashboardMetric
from .serializers import BIReportSerializer, DashboardMetricSerializer


class BaseBIViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        tenant_id = getattr(self.request, "tenant_id", None)
        return self.queryset.filter(tenant_id=tenant_id)

    def perform_create(self, serializer):
        tenant_id = getattr(self.request, "tenant_id", None)
        serializer.save(tenant_id=tenant_id)


class BIReportViewSet(BaseBIViewSet):
    queryset = BIReport.objects.all()
    serializer_class = BIReportSerializer


class DashboardMetricViewSet(BaseBIViewSet):
    queryset = DashboardMetric.objects.all()
    serializer_class = DashboardMetricSerializer
