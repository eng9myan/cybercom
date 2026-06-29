from django.db import models as db_models
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import (
    CommercialMetricsSnapshot,
    CompetitiveBenchmark,
    ComplianceCertification,
    ConcurrentLicenseSession,
    CustomerPortalAccess,
    FeatureFlag,
    License,
    LicenseKey,
    MarketplaceInstallation,
    MarketplaceListing,
    PricingPlan,
    ProductEdition,
    Proposal,
    Quotation,
    Subscription,
    SupportTicket,
    TenantFeatureFlagOverride,
    WhiteLabelConfig,
)
from .serializers import (
    CommercialMetricsSnapshotSerializer,
    CompetitiveBenchmarkSerializer,
    ComplianceCertificationSerializer,
    ConcurrentLicenseSessionSerializer,
    CustomerPortalAccessSerializer,
    FeatureFlagSerializer,
    LicenseKeySerializer,
    LicenseSerializer,
    MarketplaceInstallationSerializer,
    MarketplaceListingSerializer,
    PricingPlanSerializer,
    ProductEditionSerializer,
    ProposalSerializer,
    QuotationSerializer,
    SubscriptionSerializer,
    SupportTicketSerializer,
    TenantFeatureFlagOverrideSerializer,
    WhiteLabelConfigSerializer,
)


class BaseViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]

    def get_queryset(self):
        tenant_id = getattr(self.request, "tenant_id", None)
        if tenant_id:
            return self.queryset.filter(tenant_id=tenant_id)
        return self.queryset.none()

    def perform_create(self, serializer):
        serializer.save(tenant_id=getattr(self.request, "tenant_id", None))


class PricingPlanViewSet(BaseViewSet):
    queryset = PricingPlan.objects.all()
    serializer_class = PricingPlanSerializer
    filterset_fields = ["product_code", "plan_type", "billing_cycle", "is_active", "currency"]
    search_fields = ["name", "code"]
    ordering_fields = ["name", "base_price", "plan_type", "created_at"]


class QuotationViewSet(BaseViewSet):
    queryset = Quotation.objects.all()
    serializer_class = QuotationSerializer
    filterset_fields = ["status", "sales_rep_id", "currency"]
    search_fields = ["quote_number", "customer_name", "customer_email", "customer_organization"]
    ordering_fields = ["quote_number", "total", "valid_until", "created_at"]

    @action(detail=True, methods=["post"])
    def send(self, request, pk=None):
        quotation = self.get_object()
        quotation.status = "sent"
        quotation.save(update_fields=["status", "updated_at"])
        return Response({"status": "sent", "id": str(quotation.id)})

    @action(detail=True, methods=["post"])
    def accept(self, request, pk=None):
        quotation = self.get_object()
        quotation.status = "accepted"
        quotation.accepted_at = timezone.now()
        quotation.save(update_fields=["status", "accepted_at", "updated_at"])
        return Response(
            {"status": "accepted", "accepted_at": quotation.accepted_at, "id": str(quotation.id)}
        )

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        quotation = self.get_object()
        quotation.status = "rejected"
        quotation.save(update_fields=["status", "updated_at"])
        return Response({"status": "rejected", "id": str(quotation.id)})


class ProposalViewSet(BaseViewSet):
    queryset = Proposal.objects.all()
    serializer_class = ProposalSerializer
    filterset_fields = ["status", "currency"]
    search_fields = ["proposal_title", "customer_name", "opportunity_id", "rfp_reference"]
    ordering_fields = [
        "proposal_title",
        "total_value",
        "submission_date",
        "decision_date",
        "created_at",
    ]

    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        proposal = self.get_object()
        proposal.status = "submitted"
        if not proposal.submission_date:
            proposal.submission_date = timezone.now().date()
        proposal.save(update_fields=["status", "submission_date", "updated_at"])
        return Response({"status": "submitted", "id": str(proposal.id)})

    @action(detail=True, methods=["post"])
    def mark_won(self, request, pk=None):
        proposal = self.get_object()
        proposal.status = "won"
        proposal.win_reason = request.data.get("win_reason", proposal.win_reason)
        if not proposal.decision_date:
            proposal.decision_date = timezone.now().date()
        proposal.save(update_fields=["status", "win_reason", "decision_date", "updated_at"])
        return Response({"status": "won", "id": str(proposal.id)})

    @action(detail=True, methods=["post"])
    def mark_lost(self, request, pk=None):
        proposal = self.get_object()
        proposal.status = "lost"
        proposal.loss_reason = request.data.get("loss_reason", proposal.loss_reason)
        if not proposal.decision_date:
            proposal.decision_date = timezone.now().date()
        proposal.save(update_fields=["status", "loss_reason", "decision_date", "updated_at"])
        return Response({"status": "lost", "id": str(proposal.id)})


class LicenseKeyViewSet(BaseViewSet):
    queryset = LicenseKey.objects.all()
    serializer_class = LicenseKeySerializer
    filterset_fields = ["customer_id", "product_code", "edition", "is_active"]
    search_fields = ["key_value", "product_code", "edition"]
    ordering_fields = ["issued_at", "expires_at", "created_at"]

    @action(detail=True, methods=["post"])
    def activate(self, request, pk=None):
        license_key = self.get_object()
        license_key.is_active = True
        license_key.activated_at = timezone.now()
        license_key.save(update_fields=["is_active", "activated_at", "updated_at"])
        return Response(
            {"is_active": True, "activated_at": license_key.activated_at, "id": str(license_key.id)}
        )

    @action(detail=True, methods=["post"])
    def deactivate(self, request, pk=None):
        license_key = self.get_object()
        license_key.is_active = False
        license_key.save(update_fields=["is_active", "updated_at"])
        return Response({"is_active": False, "id": str(license_key.id)})


class ComplianceCertificationViewSet(BaseViewSet):
    queryset = ComplianceCertification.objects.all()
    serializer_class = ComplianceCertificationSerializer
    filterset_fields = ["product_code", "standard", "status"]
    search_fields = ["product_code", "auditor_name", "scope_description"]
    ordering_fields = ["standard", "certified_at", "expires_at", "created_at"]


class CompetitiveBenchmarkViewSet(BaseViewSet):
    queryset = CompetitiveBenchmark.objects.all()
    serializer_class = CompetitiveBenchmarkSerializer
    filterset_fields = ["product_code", "category", "competitor_name"]
    search_fields = ["competitor_name", "benchmark_notes", "product_code"]
    ordering_fields = ["our_score", "competitor_score", "last_updated", "created_at"]


class LicenseViewSet(BaseViewSet):
    queryset = License.objects.all()
    serializer_class = LicenseSerializer
    filterset_fields = ["status", "product_code", "edition", "license_type"]
    search_fields = ["license_key", "issued_to", "issued_to_email"]
    ordering_fields = ["created_at", "valid_until", "status"]

    def get_queryset(self):
        qs = super().get_queryset()
        return (
            qs.filter(tenant_id=getattr(self.request, "tenant_id", None))
            if getattr(self.request, "tenant_id", None)
            else qs.none()
        )

    @action(detail=True, methods=["post"])
    def activate(self, request, pk=None):
        license = self.get_object()
        license.status = "active"
        license.activated_at = timezone.now()
        license.save(update_fields=["status", "activated_at", "updated_at"])
        return Response({"status": "activated"})

    @action(detail=True, methods=["post"])
    def deactivate(self, request, pk=None):
        license = self.get_object()
        license.status = "suspended"
        license.save(update_fields=["status", "updated_at"])
        return Response({"status": "suspended"})

    @action(detail=True, methods=["post"])
    def renew(self, request, pk=None):
        license = self.get_object()
        from dateutil.relativedelta import relativedelta

        if license.valid_until:
            license.valid_until = license.valid_until + relativedelta(years=1)
        license.status = "active"
        license.save(update_fields=["status", "valid_until", "updated_at"])
        return Response({"status": "renewed", "valid_until": license.valid_until})

    @action(detail=True, methods=["post"])
    def suspend(self, request, pk=None):
        license = self.get_object()
        license.status = "suspended"
        license.save(update_fields=["status", "updated_at"])
        return Response({"status": "suspended"})

    @action(detail=True, methods=["post"])
    def generate_offline_token(self, request, pk=None):
        license = self.get_object()
        token = license.generate_offline_token()
        license.save(update_fields=["offline_token"])
        return Response({"offline_token": token, "valid_days": license.offline_valid_days})


class SubscriptionViewSet(BaseViewSet):
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer
    filterset_fields = ["status", "billing_cycle"]
    ordering_fields = ["created_at", "current_period_end"]

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        sub = self.get_object()
        sub.cancel_at_period_end = True
        sub.canceled_at = timezone.now()
        sub.save(update_fields=["cancel_at_period_end", "canceled_at", "updated_at"])
        return Response({"status": "cancellation_scheduled"})

    @action(detail=True, methods=["post"])
    def resume(self, request, pk=None):
        sub = self.get_object()
        sub.cancel_at_period_end = False
        sub.canceled_at = None
        sub.status = "active"
        sub.save(update_fields=["cancel_at_period_end", "canceled_at", "status", "updated_at"])
        return Response({"status": "resumed"})


class ProductEditionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ProductEdition.objects.filter(is_active=True)
    serializer_class = ProductEditionSerializer
    filterset_fields = ["product_code", "edition_code"]
    ordering_fields = ["product_code", "sort_order"]
    permission_classes = []  # public read


class FeatureFlagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = FeatureFlag.objects.filter(is_enabled=True)
    serializer_class = FeatureFlagSerializer
    filterset_fields = ["product_code", "edition_code"]
    permission_classes = []


class TenantFeatureFlagOverrideViewSet(BaseViewSet):
    queryset = TenantFeatureFlagOverride.objects.all()
    serializer_class = TenantFeatureFlagOverrideSerializer
    filterset_fields = ["flag", "is_enabled"]


class WhiteLabelConfigViewSet(BaseViewSet):
    queryset = WhiteLabelConfig.objects.all()
    serializer_class = WhiteLabelConfigSerializer


class ConcurrentLicenseSessionViewSet(BaseViewSet):
    queryset = ConcurrentLicenseSession.objects.all()
    serializer_class = ConcurrentLicenseSessionSerializer
    filterset_fields = ["license", "is_active"]

    @action(detail=True, methods=["post"])
    def checkin(self, request, pk=None):
        session = self.get_object()
        session.is_active = True
        session.ended_at = None
        session.save(update_fields=["is_active", "ended_at", "last_heartbeat_at"])
        return Response({"status": "checked_in"})

    @action(detail=True, methods=["post"])
    def checkout(self, request, pk=None):
        session = self.get_object()
        session.is_active = False
        session.ended_at = timezone.now()
        session.save(update_fields=["is_active", "ended_at"])
        return Response({"status": "checked_out"})


class CustomerPortalAccessViewSet(BaseViewSet):
    queryset = CustomerPortalAccess.objects.all()
    serializer_class = CustomerPortalAccessSerializer
    filterset_fields = ["access_level", "is_active"]
    search_fields = ["user_id"]


class SupportTicketViewSet(BaseViewSet):
    queryset = SupportTicket.objects.all()
    serializer_class = SupportTicketSerializer
    filterset_fields = ["status", "priority", "product_code"]
    search_fields = ["ticket_number", "subject"]
    ordering_fields = ["created_at", "priority", "sla_due_at"]

    def perform_create(self, serializer):
        import uuid

        ticket_number = f"TKT-{str(uuid.uuid4().hex[:8]).upper()}"
        serializer.save(
            tenant_id=getattr(self.request, "tenant_id", None),
            ticket_number=ticket_number,
            submitted_by_id=getattr(self.request.user, "id", None),
        )

    @action(detail=True, methods=["post"])
    def resolve(self, request, pk=None):
        ticket = self.get_object()
        ticket.status = "resolved"
        ticket.resolved_at = timezone.now()
        ticket.resolution_notes = request.data.get("resolution_notes", "")
        ticket.save(update_fields=["status", "resolved_at", "resolution_notes", "updated_at"])
        return Response({"status": "resolved"})

    @action(detail=True, methods=["post"])
    def close(self, request, pk=None):
        ticket = self.get_object()
        ticket.status = "closed"
        ticket.save(update_fields=["status", "updated_at"])
        return Response({"status": "closed"})

    @action(detail=True, methods=["post"])
    def assign(self, request, pk=None):
        ticket = self.get_object()
        ticket.assigned_to_id = request.data.get("assigned_to_id")
        ticket.status = "in_progress"
        ticket.save(update_fields=["assigned_to_id", "status", "updated_at"])
        return Response({"status": "assigned"})


class MarketplaceListingViewSet(viewsets.ModelViewSet):
    queryset = MarketplaceListing.objects.filter(status="published")
    serializer_class = MarketplaceListingSerializer
    filterset_fields = ["category", "publisher_type", "price_model", "is_featured"]
    search_fields = ["name", "description", "tags"]
    ordering_fields = ["install_count", "rating_avg", "published_at"]

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return []
        return super().get_permissions()

    @action(detail=True, methods=["post"])
    def install(self, request, pk=None):
        listing = self.get_object()
        tenant_id = getattr(request, "tenant_id", None)
        if not tenant_id:
            return Response({"error": "Tenant context required"}, status=400)
        installation, created = MarketplaceInstallation.objects.get_or_create(
            tenant_id=tenant_id,
            listing=listing,
            defaults={
                "installed_by_id": getattr(request.user, "id", None),
                "installed_version": listing.version,
                "is_active": True,
            },
        )
        if not created:
            installation.is_active = True
            installation.save(update_fields=["is_active"])
        listing.install_count = db_models.F("install_count") + 1
        listing.save(update_fields=["install_count"])
        return Response({"status": "installed", "installation_id": str(installation.id)})


class MarketplaceInstallationViewSet(BaseViewSet):
    queryset = MarketplaceInstallation.objects.all()
    serializer_class = MarketplaceInstallationSerializer
    filterset_fields = ["listing", "is_active"]


class CommercialMetricsSnapshotViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = CommercialMetricsSnapshot.objects.all()
    serializer_class = CommercialMetricsSnapshotSerializer
    filterset_fields = ["metric_type", "product_code", "snapshot_date"]
    ordering_fields = ["snapshot_date"]
