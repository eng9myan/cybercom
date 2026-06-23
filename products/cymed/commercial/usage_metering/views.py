from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone

from products.cymed.commercial.views import CommercialModelViewSet
from products.cymed.commercial.usage_metering.models import UsageMeter, UsageAlert
from products.cymed.commercial.usage_metering.serializers import UsageMeterSerializer, UsageAlertSerializer


class UsageMeterViewSet(CommercialModelViewSet):
    queryset = UsageMeter.objects.all()
    serializer_class = UsageMeterSerializer

    def get_queryset(self):
        tenant_id = getattr(self.request, "tenant_id", None)
        if tenant_id:
            return UsageMeter.objects.filter(tenant_id=tenant_id).order_by("-snapshot_date")
        return UsageMeter.objects.all().order_by("-snapshot_date")


class UsageAlertViewSet(CommercialModelViewSet):
    queryset = UsageAlert.objects.all()
    serializer_class = UsageAlertSerializer


class UsageDashboardView(APIView):
    """Platform-level usage dashboard for commercial admin."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        today = timezone.now().date()
        tenant_id = getattr(request, "tenant_id", None)

        qs = UsageMeter.objects.filter(snapshot_date=today)
        if tenant_id:
            qs = qs.filter(tenant_id=tenant_id)

        meters = list(qs)
        total_users = sum(m.active_users for m in meters)
        total_providers = sum(m.active_providers for m in meters)
        total_beds = sum(m.occupied_beds for m in meters)
        total_api = sum(m.api_calls for m in meters)
        over_limit = [m for m in meters if m.is_over_user_limit or m.is_over_bed_limit]

        return Response({
            "snapshot_date": str(today),
            "summary": {
                "total_active_users": total_users,
                "total_active_providers": total_providers,
                "total_occupied_beds": total_beds,
                "total_api_calls_today": total_api,
                "tenants_over_limit": len(over_limit),
            }
        })
