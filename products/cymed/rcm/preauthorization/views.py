from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response

from .models import (
    AuthorizationAppeal,
    AuthorizationDecision,
    AuthorizationRequest,
    Preauthorization,
)
from .serializers import (
    AuthorizationAppealSerializer,
    AuthorizationDecisionSerializer,
    AuthorizationRequestSerializer,
    PreauthorizationSerializer,
)


class PreauthorizationViewSet(viewsets.ModelViewSet):
    queryset = Preauthorization.objects.all()
    serializer_class = PreauthorizationSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = [
        "patient_id",
        "status",
        "authorization_type",
        "insurance_plan_id",
        "priority",
        "requesting_provider_id",
    ]
    search_fields = ["service_description", "auth_number"]
    ordering_fields = ["created_at", "requested_start_date", "status"]
    ordering = ["-created_at"]

    def get_queryset(self):
        tenant_id = self.request.headers.get("X-Tenant-ID")
        if tenant_id:
            return self.queryset.filter(tenant_id=tenant_id)
        return self.queryset

    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        preauth = self.get_object()
        if preauth.status not in ("draft",):
            return Response(
                {"error": "Only draft preauthorizations can be submitted."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        preauth.status = "submitted"
        preauth.save()
        return Response({"status": "submitted", "id": str(preauth.id)})

    @action(detail=True, methods=["post"])
    def renew(self, request, pk=None):
        preauth = self.get_object()
        if preauth.status not in ("approved", "expired"):
            return Response(
                {"error": "Only approved or expired authorizations can be renewed."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        preauth.status = "submitted"
        preauth.auth_number = None
        preauth.approved_units = None
        preauth.approved_start_date = None
        preauth.approved_end_date = None
        preauth.save()
        return Response({"status": "renewal_submitted", "id": str(preauth.id)})


class AuthorizationRequestViewSet(viewsets.ModelViewSet):
    queryset = AuthorizationRequest.objects.all()
    serializer_class = AuthorizationRequestSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["preauthorization", "submission_method"]
    ordering = ["-request_date"]

    def get_queryset(self):
        tenant_id = self.request.headers.get("X-Tenant-ID")
        if tenant_id:
            return self.queryset.filter(tenant_id=tenant_id)
        return self.queryset


class AuthorizationDecisionViewSet(viewsets.ModelViewSet):
    queryset = AuthorizationDecision.objects.all()
    serializer_class = AuthorizationDecisionSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["preauthorization", "decision"]
    ordering = ["-decision_date"]

    def get_queryset(self):
        tenant_id = self.request.headers.get("X-Tenant-ID")
        if tenant_id:
            return self.queryset.filter(tenant_id=tenant_id)
        return self.queryset


class AuthorizationAppealViewSet(viewsets.ModelViewSet):
    queryset = AuthorizationAppeal.objects.all()
    serializer_class = AuthorizationAppealSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["preauthorization", "status", "appeal_level"]
    ordering = ["-appeal_date"]

    def get_queryset(self):
        tenant_id = self.request.headers.get("X-Tenant-ID")
        if tenant_id:
            return self.queryset.filter(tenant_id=tenant_id)
        return self.queryset

    @action(detail=True, methods=["post"])
    def submit_appeal(self, request, pk=None):
        appeal = self.get_object()
        if appeal.status != "submitted":
            appeal.status = "submitted"
            appeal.save()
        return Response({"status": "submitted", "id": str(appeal.id)})
