from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from .models import PayerPortalAccount, PayerDashboard, PayerClaimReview, PayerAuthorizationReview
from .serializers import (
    PayerPortalAccountSerializer, PayerDashboardSerializer,
    PayerClaimReviewSerializer, PayerAuthorizationReviewSerializer,
)


class PayerPortalAccountViewSet(viewsets.ModelViewSet):
    queryset = PayerPortalAccount.objects.all()
    serializer_class = PayerPortalAccountSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["insurance_company_id", "account_role", "is_active", "access_level"]
    ordering = ["-created_at"]

    def get_queryset(self):
        tenant_id = self.request.headers.get("X-Tenant-ID")
        if tenant_id:
            return self.queryset.filter(tenant_id=tenant_id)
        return self.queryset


class PayerDashboardViewSet(viewsets.ModelViewSet):
    queryset = PayerDashboard.objects.all()
    serializer_class = PayerDashboardSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["payer_account"]

    def get_queryset(self):
        tenant_id = self.request.headers.get("X-Tenant-ID")
        if tenant_id:
            return self.queryset.filter(tenant_id=tenant_id)
        return self.queryset


class PayerClaimReviewViewSet(viewsets.ModelViewSet):
    queryset = PayerClaimReview.objects.all()
    serializer_class = PayerClaimReviewSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["payer_account", "review_status", "decision"]
    ordering = ["-created_at"]

    def get_queryset(self):
        tenant_id = self.request.headers.get("X-Tenant-ID")
        if tenant_id:
            return self.queryset.filter(tenant_id=tenant_id)
        return self.queryset

    @action(detail=True, methods=["post"])
    def make_decision(self, request, pk=None):
        review = self.get_object()
        decision = request.data.get("decision")
        if decision not in ("approved", "denied", "partial", "pending"):
            return Response({"error": "Invalid decision value."}, status=status.HTTP_400_BAD_REQUEST)
        review.decision = decision
        review.decision_date = timezone.now()
        review.review_status = "decision_made"
        review.reviewer_notes = request.data.get("reviewer_notes", review.reviewer_notes)
        review.save()
        return Response({"status": "decision_recorded", "decision": decision})


class PayerAuthorizationReviewViewSet(viewsets.ModelViewSet):
    queryset = PayerAuthorizationReview.objects.all()
    serializer_class = PayerAuthorizationReviewSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["payer_account", "review_status", "decision"]
    ordering = ["-created_at"]

    def get_queryset(self):
        tenant_id = self.request.headers.get("X-Tenant-ID")
        if tenant_id:
            return self.queryset.filter(tenant_id=tenant_id)
        return self.queryset

    @action(detail=True, methods=["post"])
    def make_decision(self, request, pk=None):
        review = self.get_object()
        decision = request.data.get("decision")
        if decision not in ("approved", "partially_approved", "denied", "pending_info"):
            return Response({"error": "Invalid decision value."}, status=status.HTTP_400_BAD_REQUEST)
        review.decision = decision
        review.decision_date = timezone.now()
        review.review_status = "decision_made"
        review.approved_units = request.data.get("approved_units", review.approved_units)
        review.approved_start_date = request.data.get("approved_start_date", review.approved_start_date)
        review.approved_end_date = request.data.get("approved_end_date", review.approved_end_date)
        review.reviewer_notes = request.data.get("reviewer_notes", review.reviewer_notes)
        review.save()
        return Response({"status": "decision_recorded", "decision": decision})
