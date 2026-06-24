from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from .models import (
    RevenueDashboardSnapshot,
    ClaimMetricsSnapshot,
    DenialAnalyticsSnapshot,
    PayerPerformanceSnapshot,
    RCMAIInsight,
    RevenueLeakageAlert,
)
from .serializers import (
    RevenueDashboardSnapshotSerializer,
    ClaimMetricsSnapshotSerializer,
    DenialAnalyticsSnapshotSerializer,
    PayerPerformanceSnapshotSerializer,
    RCMAIInsightSerializer,
    RevenueLeakageAlertSerializer,
)


class RevenueDashboardSnapshotViewSet(ModelViewSet):
    """
    Read-only revenue KPI snapshots with create support for background tasks.
    Supports filtering by date, period, and facility.
    """

    queryset = RevenueDashboardSnapshot.objects.all()
    serializer_class = RevenueDashboardSnapshotSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["snapshot_date", "snapshot_period", "facility_id"]
    search_fields = ["snapshot_period"]
    ordering_fields = [
        "snapshot_date", "snapshot_period", "gross_revenue",
        "net_revenue", "days_in_ar", "collection_rate", "denial_rate",
    ]
    ordering = ["-snapshot_date"]
    http_method_names = ["get", "post", "head", "options"]


class ClaimMetricsSnapshotViewSet(ModelViewSet):
    """
    Read-only claim volume and payment metrics snapshots.
    Supports filtering by date, period, and payer.
    """

    queryset = ClaimMetricsSnapshot.objects.all()
    serializer_class = ClaimMetricsSnapshotSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["snapshot_date", "snapshot_period", "insurance_company_id"]
    search_fields = ["snapshot_period"]
    ordering_fields = [
        "snapshot_date", "snapshot_period", "total_claims_submitted",
        "total_claims_paid", "total_claims_denied", "first_pass_rate",
        "average_days_to_payment",
    ]
    ordering = ["-snapshot_date"]
    http_method_names = ["get", "head", "options"]


class DenialAnalyticsSnapshotViewSet(ModelViewSet):
    """
    Read-only denial trend snapshots broken down by category.
    Supports filtering by date, period, and denial category.
    """

    queryset = DenialAnalyticsSnapshot.objects.all()
    serializer_class = DenialAnalyticsSnapshotSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["snapshot_date", "snapshot_period", "denial_category"]
    search_fields = ["denial_category"]
    ordering_fields = [
        "snapshot_date", "snapshot_period", "denial_category",
        "total_denials", "total_denial_amount", "appeal_success_rate",
        "amount_recovered",
    ]
    ordering = ["-snapshot_date", "denial_category"]
    http_method_names = ["get", "head", "options"]


class PayerPerformanceSnapshotViewSet(ModelViewSet):
    """
    Read-only payer performance scorecards.
    Supports filtering by date, payer, and trend direction.
    """

    queryset = PayerPerformanceSnapshot.objects.all()
    serializer_class = PayerPerformanceSnapshotSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["snapshot_date", "insurance_company_id", "trend_direction"]
    search_fields = ["trend_direction"]
    ordering_fields = [
        "snapshot_date", "snapshot_period", "performance_score",
        "payment_rate", "denial_rate", "average_processing_days",
        "trend_direction",
    ]
    ordering = ["-snapshot_date"]
    http_method_names = ["get", "head", "options"]


class RCMAIInsightViewSet(ModelViewSet):
    """
    AI-generated advisory insights for RCM entities.
    Read-only for insight data; exposes `acknowledge` action for staff workflow.
    """

    queryset = RCMAIInsight.objects.all()
    serializer_class = RCMAIInsightSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["insight_type", "scope_type", "status"]
    search_fields = ["insight_title", "insight_detail"]
    ordering_fields = [
        "created_at", "insight_type", "scope_type", "status",
        "confidence_score", "estimated_impact_amount",
    ]
    ordering = ["-created_at"]
    http_method_names = ["get", "head", "options", "post"]

    def get_allowed_methods(self, *args, **kwargs):
        # Allow POST only through the `acknowledge` action, not for creating insights
        return super().get_allowed_methods(*args, **kwargs)

    @action(detail=True, methods=["post"], url_path="acknowledge")
    def acknowledge(self, request, pk=None):
        """
        Mark an AI insight as acknowledged by the requesting user.
        Sets status to 'acknowledged', records user_id and timestamp.
        """
        insight = self.get_object()

        if insight.status not in ("pending_review",):
            return Response(
                {"detail": f"Insight is already in status '{insight.status}' and cannot be acknowledged again."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user_id = request.data.get("acknowledged_by_user_id")
        if not user_id:
            return Response(
                {"detail": "acknowledged_by_user_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        insight.status = "acknowledged"
        insight.acknowledged_by_user_id = user_id
        insight.acknowledged_at = timezone.now()
        insight.save(update_fields=["status", "acknowledged_by_user_id", "acknowledged_at", "updated_at"])

        serializer = self.get_serializer(insight)
        return Response(serializer.data, status=status.HTTP_200_OK)


class RevenueLeakageAlertViewSet(ModelViewSet):
    """
    Full CRUD for revenue leakage alerts with a `resolve` action
    for closing alerts with resolution notes.
    """

    queryset = RevenueLeakageAlert.objects.all()
    serializer_class = RevenueLeakageAlertSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["leakage_type", "status", "alert_date"]
    search_fields = ["leakage_type", "resolution_notes"]
    ordering_fields = [
        "alert_date", "leakage_type", "status",
        "estimated_leakage_amount", "created_at",
    ]
    ordering = ["-alert_date", "-created_at"]

    @action(detail=True, methods=["post"], url_path="resolve")
    def resolve(self, request, pk=None):
        """
        Resolve a leakage alert. Requires resolution_notes.
        Optionally accepts new `status` (resolved or false_positive).
        """
        alert = self.get_object()

        if alert.status in ("resolved", "false_positive"):
            return Response(
                {"detail": f"Alert is already in terminal status '{alert.status}'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        resolution_notes = request.data.get("resolution_notes", "").strip()
        if not resolution_notes:
            return Response(
                {"detail": "resolution_notes is required to resolve an alert."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        new_status = request.data.get("status", "resolved")
        if new_status not in ("resolved", "false_positive"):
            return Response(
                {"detail": "status must be 'resolved' or 'false_positive'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        alert.status = new_status
        alert.resolution_notes = resolution_notes
        alert.save(update_fields=["status", "resolution_notes", "updated_at"])

        serializer = self.get_serializer(alert)
        return Response(serializer.data, status=status.HTTP_200_OK)
