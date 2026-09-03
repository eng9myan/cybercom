from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import ProviderCredentialingStatus, ProviderPortalActivity, ProviderPortalProfile
from .serializers import (
    ProviderCredentialingStatusSerializer,
    ProviderPortalActivitySerializer,
    ProviderPortalProfileSerializer,
)


class ProviderPortalProfileViewSet(viewsets.ModelViewSet):
    queryset = ProviderPortalProfile.objects.all()
    serializer_class = ProviderPortalProfileSerializer

    @action(detail=True, methods=["post"], url_path="toggle-on-call")
    def toggle_on_call(self, request, pk=None):
        profile = self.get_object()
        profile.is_on_call = not profile.is_on_call
        profile.save(update_fields=["is_on_call"])
        return Response({"is_on_call": profile.is_on_call})

    @action(detail=True, methods=["get"], url_path="activities")
    def activities(self, request, pk=None):
        profile = self.get_object()
        qs = profile.activities.all()[:50]
        serializer = ProviderPortalActivitySerializer(qs, many=True)
        return Response(serializer.data)


class ProviderPortalActivityViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ProviderPortalActivity.objects.all()
    serializer_class = ProviderPortalActivitySerializer


class ProviderCredentialingStatusViewSet(viewsets.ModelViewSet):
    queryset = ProviderCredentialingStatus.objects.all()
    serializer_class = ProviderCredentialingStatusSerializer

    @action(detail=True, methods=["post"], url_path="verify")
    def verify(self, request, pk=None):
        obj = self.get_object()
        from django.utils import timezone

        obj.status = "verified"
        obj.verified_at = timezone.now()
        obj.verified_by = request.data.get("verified_by", "")
        obj.license_verified = request.data.get("license_verified", obj.license_verified)
        obj.board_certification_verified = request.data.get(
            "board_certification_verified", obj.board_certification_verified
        )
        obj.background_check_passed = request.data.get(
            "background_check_passed", obj.background_check_passed
        )
        obj.malpractice_insurance_verified = request.data.get(
            "malpractice_insurance_verified", obj.malpractice_insurance_verified
        )
        obj.save()
        return Response(ProviderCredentialingStatusSerializer(obj).data)
