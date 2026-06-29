"""CyMed Pharmacy — Analytics Views."""

from datetime import timedelta

from django.db.models import Count
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ..views import PharmacyModelViewSet
from .models import MedicationSafetyEvent, PharmacyAnalyticsConfig, PharmacyDashboardSnapshot
from .serializers import (
    MedicationSafetyEventSerializer,
    PharmacyAnalyticsConfigSerializer,
    PharmacyDashboardSnapshotSerializer,
)


class PharmacyDashboardSnapshotViewSet(PharmacyModelViewSet):
    queryset = PharmacyDashboardSnapshot.objects.all()
    serializer_class = PharmacyDashboardSnapshotSerializer
    required_feature = "pharmacy.analytics"
    filterset_fields = ["snapshot_type", "snapshot_date"]
    ordering = ["-snapshot_date"]


class MedicationSafetyEventViewSet(PharmacyModelViewSet):
    queryset = MedicationSafetyEvent.objects.all()
    serializer_class = MedicationSafetyEventSerializer
    required_feature = "pharmacy.analytics"
    filterset_fields = ["event_type", "severity", "is_reported_to_authority"]
    ordering = ["-occurred_at"]


class PharmacyAnalyticsConfigViewSet(PharmacyModelViewSet):
    queryset = PharmacyAnalyticsConfig.objects.all()
    serializer_class = PharmacyAnalyticsConfigSerializer
    required_feature = "pharmacy.analytics"
    filterset_fields = ["dashboard_type", "is_active"]


class PharmacyOperationsDashboardView(APIView):
    """
    Real-time pharmacy operations dashboard.
    Aggregates live data from prescriptions, dispensing, and interactions.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        tenant_id = getattr(request, "tenant_id", None)
        now = timezone.now()
        today = now.date()
        last_24h = now - timedelta(hours=24)

        from products.cymed.pharmacy.dispensing.models import DispenseOrder
        from products.cymed.pharmacy.drug_interactions.models import DrugInteraction
        from products.cymed.pharmacy.prescriptions.models import Prescription

        rx_qs = Prescription.objects.filter(tenant_id=tenant_id)
        dispense_qs = DispenseOrder.objects.filter(tenant_id=tenant_id)
        interaction_qs = DrugInteraction.objects.filter(tenant_id=tenant_id)

        return Response(
            {
                "timestamp": now.isoformat(),
                "prescriptions": {
                    "total_today": rx_qs.filter(prescribed_at__date=today).count(),
                    "pending": rx_qs.filter(status="pending").count(),
                    "active": rx_qs.filter(status="active").count(),
                    "controlled": rx_qs.filter(
                        is_controlled=True, prescribed_at__date=today
                    ).count(),
                },
                "dispensing": {
                    "queued": dispense_qs.filter(status="queued").count(),
                    "in_progress": dispense_qs.filter(status="in_progress").count(),
                    "pending_verification": dispense_qs.filter(
                        status="verification_pending"
                    ).count(),
                    "completed_today": dispense_qs.filter(dispensed_at__date=today).count(),
                },
                "interactions": {
                    "active_alerts": interaction_qs.filter(alert_status="active").count(),
                    "severe": interaction_qs.filter(
                        alert_status="active", severity="severe"
                    ).count(),
                    "contraindicated": interaction_qs.filter(
                        alert_status="active", severity="contraindicated"
                    ).count(),
                    "detected_24h": interaction_qs.filter(detected_at__gte=last_24h).count(),
                },
            }
        )


class MedicationSafetyDashboardView(APIView):
    """Medication safety dashboard aggregations."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        tenant_id = getattr(request, "tenant_id", None)
        days = int(request.query_params.get("days", 30))
        from_date = timezone.now() - timedelta(days=days)

        qs = MedicationSafetyEvent.objects.filter(tenant_id=tenant_id, occurred_at__gte=from_date)
        by_type = qs.values("event_type").annotate(count=Count("id"))
        by_severity = qs.values("severity").annotate(count=Count("id"))

        return Response(
            {
                "period_days": days,
                "total_events": qs.count(),
                "by_type": list(by_type),
                "by_severity": list(by_severity),
                "unreported": qs.filter(is_reported_to_authority=False).count(),
            }
        )
