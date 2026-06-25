from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import (
    PricingPlan, Quotation, Proposal, LicenseKey,
    ComplianceCertification, CompetitiveBenchmark,
)
from .serializers import (
    PricingPlanSerializer, QuotationSerializer, ProposalSerializer, LicenseKeySerializer,
    ComplianceCertificationSerializer, CompetitiveBenchmarkSerializer,
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
        return Response({"status": "accepted", "accepted_at": quotation.accepted_at, "id": str(quotation.id)})

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
    ordering_fields = ["proposal_title", "total_value", "submission_date", "decision_date", "created_at"]

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
        return Response({"is_active": True, "activated_at": license_key.activated_at, "id": str(license_key.id)})

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
