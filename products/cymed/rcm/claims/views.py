from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from .models import Claim, ClaimLine, ClaimSubmission, ClaimResponse, ClaimStatus, ClaimAttachment
from .serializers import (
    ClaimSerializer, ClaimLineSerializer, ClaimSubmissionSerializer,
    ClaimResponseSerializer, ClaimStatusSerializer, ClaimAttachmentSerializer,
)


class ClaimViewSet(viewsets.ModelViewSet):
    queryset = Claim.objects.all()
    serializer_class = ClaimSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["patient_id", "insurance_plan_id", "status", "claim_type", "claim_date", "is_resubmission"]
    search_fields = ["claim_number", "icd11_primary_diagnosis"]
    ordering_fields = ["created_at", "claim_date", "status"]
    ordering = ["-created_at"]

    def get_queryset(self):
        tenant_id = self.request.headers.get("X-Tenant-ID")
        if tenant_id:
            return self.queryset.filter(tenant_id=tenant_id)
        return self.queryset

    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        claim = self.get_object()
        if claim.status not in ("draft", "ready"):
            return Response({"error": "Claim must be in draft or ready status to submit."}, status=status.HTTP_400_BAD_REQUEST)
        claim.status = "submitted"
        claim.save()
        ClaimStatus.objects.create(
            tenant_id=claim.tenant_id,
            claim=claim,
            previous_status="ready",
            new_status="submitted",
            changed_by_user_id=request.data.get("submitted_by_user_id"),
        )
        return Response({"status": "submitted", "id": str(claim.id)})

    @action(detail=True, methods=["post"])
    def resubmit(self, request, pk=None):
        claim = self.get_object()
        if claim.status not in ("denied",):
            return Response({"error": "Only denied claims can be resubmitted."}, status=status.HTTP_400_BAD_REQUEST)
        claim.status = "resubmitted"
        claim.is_resubmission = True
        claim.original_claim_id = claim.id
        claim.save()
        return Response({"status": "resubmitted", "id": str(claim.id)})

    @action(detail=True, methods=["post"])
    def void(self, request, pk=None):
        claim = self.get_object()
        if claim.status in ("paid",):
            return Response({"error": "Paid claims cannot be voided."}, status=status.HTTP_400_BAD_REQUEST)
        claim.status = "voided"
        claim.save()
        return Response({"status": "voided", "id": str(claim.id)})


class ClaimLineViewSet(viewsets.ModelViewSet):
    queryset = ClaimLine.objects.all()
    serializer_class = ClaimLineSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["claim", "line_status"]
    ordering = ["line_number"]

    def get_queryset(self):
        tenant_id = self.request.headers.get("X-Tenant-ID")
        if tenant_id:
            return self.queryset.filter(tenant_id=tenant_id)
        return self.queryset


class ClaimSubmissionViewSet(viewsets.ModelViewSet):
    queryset = ClaimSubmission.objects.all()
    serializer_class = ClaimSubmissionSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["claim", "submission_method", "acknowledgement_received"]
    ordering = ["-submitted_at"]

    def get_queryset(self):
        tenant_id = self.request.headers.get("X-Tenant-ID")
        if tenant_id:
            return self.queryset.filter(tenant_id=tenant_id)
        return self.queryset


class ClaimResponseViewSet(viewsets.ModelViewSet):
    queryset = ClaimResponse.objects.all()
    serializer_class = ClaimResponseSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["claim", "response_type", "payment_date"]
    ordering = ["-response_date"]

    def get_queryset(self):
        tenant_id = self.request.headers.get("X-Tenant-ID")
        if tenant_id:
            return self.queryset.filter(tenant_id=tenant_id)
        return self.queryset


class ClaimStatusViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ClaimStatus.objects.all()
    serializer_class = ClaimStatusSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["claim"]
    ordering = ["-changed_at"]

    def get_queryset(self):
        tenant_id = self.request.headers.get("X-Tenant-ID")
        if tenant_id:
            return self.queryset.filter(tenant_id=tenant_id)
        return self.queryset


class ClaimAttachmentViewSet(viewsets.ModelViewSet):
    queryset = ClaimAttachment.objects.all()
    serializer_class = ClaimAttachmentSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["claim", "attachment_type"]
    ordering = ["-created_at"]

    def get_queryset(self):
        tenant_id = self.request.headers.get("X-Tenant-ID")
        if tenant_id:
            return self.queryset.filter(tenant_id=tenant_id)
        return self.queryset
