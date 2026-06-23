from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone

from products.cymed.commercial.views import CommercialModelViewSet
from products.cymed.commercial.licensing.models import (
    License, LicenseKey, LicenseActivation, LicenseFeature,
    LicenseAudit, LicenseUsage, LicenseServer, OfflineActivationPackage
)
from products.cymed.commercial.licensing.serializers import (
    LicenseSerializer, LicenseKeySerializer, LicenseActivationSerializer,
    LicenseFeatureSerializer, LicenseAuditSerializer, LicenseUsageSerializer,
    LicenseServerSerializer, OfflineActivationPackageSerializer,
    LicenseActivateSerializer, LicenseValidateSerializer
)
from platform.events.models import OutboxEvent


class LicenseViewSet(CommercialModelViewSet):
    queryset = License.objects.all()
    serializer_class = LicenseSerializer

    @action(detail=True, methods=["post"])
    def activate(self, request, pk=None):
        """Activate a license using a key string."""
        license_obj = self.get_object()
        ser = LicenseActivateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        key_string = ser.validated_data["license_key"]
        try:
            key = LicenseKey.objects.get(license=license_obj, key_string=key_string)
        except LicenseKey.DoesNotExist:
            return Response({"detail": "Invalid license key."}, status=status.HTTP_400_BAD_REQUEST)

        if not key.can_activate():
            return Response({"detail": "License key is revoked or max activations reached."}, status=status.HTTP_400_BAD_REQUEST)

        if not license_obj.is_valid():
            return Response({"detail": "License is expired or revoked."}, status=status.HTTP_403_FORBIDDEN)

        # Record activation
        activation = LicenseActivation.objects.create(
            tenant_id=license_obj.tenant_id,
            license_key=key,
            machine_fingerprint=ser.validated_data.get("machine_fingerprint", ""),
            ip_address=request.META.get("REMOTE_ADDR"),
            deployment_profile_code=ser.validated_data.get("deployment_profile_code", ""),
            is_online=ser.validated_data.get("is_online", True),
        )
        key.activation_count += 1
        key.save()

        # Audit event
        LicenseAudit.objects.create(
            tenant_id=license_obj.tenant_id,
            license=license_obj,
            event_type="activated",
            performed_by=request.user.id if hasattr(request, "user") else None,
            metadata={"key": key_string, "ip": str(request.META.get("REMOTE_ADDR"))}
        )

        # OutboxEvent
        OutboxEvent.objects.create(
            tenant_id=license_obj.tenant_id,
            topic="cymed.commercial.events",
            event_type="cymed.license.activated",
            payload={
                "license_number": license_obj.license_number,
                "product_code": license_obj.product_code,
                "edition_code": license_obj.edition_code,
                "organization_name": license_obj.organization_name,
            }
        )

        return Response({
            "status": "activated",
            "license_number": license_obj.license_number,
            "valid_until": str(license_obj.valid_until),
            "edition": license_obj.edition_code,
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"])
    def validate(self, request):
        """Validate license status for a product."""
        ser = LicenseValidateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        try:
            lic = License.objects.get(
                license_number=ser.validated_data["license_number"],
                product_code=ser.validated_data["product_code"]
            )
        except License.DoesNotExist:
            return Response({"valid": False, "reason": "License not found."}, status=status.HTTP_404_NOT_FOUND)

        is_valid = lic.is_valid()
        return Response({
            "valid": is_valid,
            "status": lic.status,
            "edition": lic.edition_code,
            "valid_until": str(lic.valid_until),
            "grace_period_days": lic.grace_period_days,
        })

    @action(detail=True, methods=["post"])
    def revoke(self, request, pk=None):
        """Revoke a license."""
        license_obj = self.get_object()
        license_obj.status = "revoked"
        license_obj.save()

        LicenseAudit.objects.create(
            tenant_id=license_obj.tenant_id,
            license=license_obj,
            event_type="revoked",
            performed_by=request.user.id if hasattr(request, "user") else None,
            metadata={"reason": request.data.get("reason", "")}
        )

        OutboxEvent.objects.create(
            tenant_id=license_obj.tenant_id,
            topic="cymed.commercial.events",
            event_type="cymed.license.revoked",
            payload={"license_number": license_obj.license_number}
        )

        return Response({"status": "revoked"})


class LicenseKeyViewSet(CommercialModelViewSet):
    queryset = LicenseKey.objects.all()
    serializer_class = LicenseKeySerializer


class LicenseActivationViewSet(CommercialModelViewSet):
    queryset = LicenseActivation.objects.all()
    serializer_class = LicenseActivationSerializer


class LicenseFeatureViewSet(CommercialModelViewSet):
    queryset = LicenseFeature.objects.all()
    serializer_class = LicenseFeatureSerializer


class LicenseAuditViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = LicenseAudit.objects.all()
    serializer_class = LicenseAuditSerializer
    permission_classes = [IsAuthenticated]


class LicenseUsageViewSet(CommercialModelViewSet):
    queryset = LicenseUsage.objects.all()
    serializer_class = LicenseUsageSerializer


class LicenseServerViewSet(CommercialModelViewSet):
    queryset = LicenseServer.objects.all()
    serializer_class = LicenseServerSerializer


class OfflineActivationPackageViewSet(CommercialModelViewSet):
    queryset = OfflineActivationPackage.objects.all()
    serializer_class = OfflineActivationPackageSerializer
