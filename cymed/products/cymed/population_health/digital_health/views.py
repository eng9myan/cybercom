from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import (
    DigitalHealthWalletEntry,
    HealthPass,
    NationalHealthID,
    VaccinationCertificate,
)
from .serializers import (
    DigitalHealthWalletEntrySerializer,
    HealthPassSerializer,
    NationalHealthIDSerializer,
    VaccinationCertificateSerializer,
)


class DigitalHealthBaseViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]

    def get_queryset(self):
        tenant_id = getattr(self.request, "tenant_id", None)
        if tenant_id:
            return self.queryset.filter(tenant_id=tenant_id)
        return self.queryset.none()

    def perform_create(self, serializer):
        tenant_id = getattr(self.request, "tenant_id", None)
        serializer.save(tenant_id=tenant_id)


class NationalHealthIDViewSet(DigitalHealthBaseViewSet):
    queryset = NationalHealthID.objects.all()
    serializer_class = NationalHealthIDSerializer
    filterset_fields = ["id_status", "id_type"]
    search_fields = ["national_id_number"]
    ordering_fields = ["issued_date", "created_at"]

    @action(detail=True, methods=["post"])
    def verify(self, request, pk=None):
        """Mark a national health ID as verified."""
        national_id = self.get_object()
        from django.utils import timezone

        national_id.id_status = "active"
        national_id.verification_date = timezone.now().date()
        national_id.verified_by_user_id = request.data.get("verified_by_user_id")
        national_id.save(
            update_fields=["id_status", "verification_date", "verified_by_user_id", "updated_at"]
        )
        return Response({"status": "verified", "id": str(national_id.id)})


class VaccinationCertificateViewSet(DigitalHealthBaseViewSet):
    queryset = VaccinationCertificate.objects.all()
    serializer_class = VaccinationCertificateSerializer
    filterset_fields = ["patient_id", "vaccine_code", "certificate_status", "is_international"]
    search_fields = ["vaccine_name", "certificate_number"]
    ordering_fields = ["vaccination_date", "created_at"]

    @action(detail=True, methods=["post"])
    def revoke(self, request, pk=None):
        """Revoke a vaccination certificate."""
        cert = self.get_object()
        cert.certificate_status = "revoked"
        cert.save(update_fields=["certificate_status", "updated_at"])
        return Response({"status": "revoked", "id": str(cert.id)})


class HealthPassViewSet(DigitalHealthBaseViewSet):
    queryset = HealthPass.objects.all()
    serializer_class = HealthPassSerializer
    filterset_fields = ["patient_id", "pass_type", "pass_status"]
    search_fields = ["pass_name", "issued_by_authority"]
    ordering_fields = ["valid_from", "created_at"]

    @action(detail=True, methods=["post"])
    def revoke(self, request, pk=None):
        """Revoke a health pass."""
        health_pass = self.get_object()
        revocation_reason = request.data.get("revocation_reason", "")
        health_pass.pass_status = "revoked"
        health_pass.revocation_reason = revocation_reason
        health_pass.save(update_fields=["pass_status", "revocation_reason", "updated_at"])
        return Response({"status": "revoked", "id": str(health_pass.id)})


class DigitalHealthWalletEntryViewSet(DigitalHealthBaseViewSet):
    queryset = DigitalHealthWalletEntry.objects.all()
    serializer_class = DigitalHealthWalletEntrySerializer
    filterset_fields = ["patient_id", "entry_type", "is_shareable", "is_verified"]
    search_fields = ["title", "issuing_authority"]
    ordering_fields = ["issue_date", "created_at"]
