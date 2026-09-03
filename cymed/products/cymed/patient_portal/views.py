import hashlib
import secrets
from datetime import timedelta

from django.utils import timezone
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    ConsentGrant,
    DelegatedAccess,
    EmergencyProfile,
    NFCCard,
    NFCScanLog,
    PatientDevice,
    PatientPortalActivity,
    PatientPortalNotificationPreference,
    PatientPortalProfile,
)
from .nfc_service import build_summary_for_purpose, issue_challenge, verify_scan
from .serializers import (
    ConsentGrantSerializer,
    DelegatedAccessSerializer,
    EmergencyProfileSerializer,
    NFCCardCreateSerializer,
    NFCCardSerializer,
    NFCScanLogSerializer,
    NFCScanPublicRequestSerializer,
    PatientDeviceSerializer,
    PatientPortalActivitySerializer,
    PatientPortalNotificationPreferenceSerializer,
    PatientPortalProfileSerializer,
)


# ── Portal profile ──────────────────────────────────────────────────────
class PatientPortalProfileViewSet(viewsets.ModelViewSet):
    queryset = PatientPortalProfile.objects.all()
    serializer_class = PatientPortalProfileSerializer

    @action(detail=True, methods=["get"], url_path="activities")
    def activities(self, request, pk=None):
        profile = self.get_object()
        qs = profile.activities.all()[:50]
        return Response(PatientPortalActivitySerializer(qs, many=True).data)

    @action(detail=True, methods=["get"], url_path="notification-preferences")
    def notification_preferences(self, request, pk=None):
        profile = self.get_object()
        qs = profile.notification_preferences.all()
        return Response(PatientPortalNotificationPreferenceSerializer(qs, many=True).data)


class PatientPortalActivityViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PatientPortalActivity.objects.all()
    serializer_class = PatientPortalActivitySerializer


class PatientPortalNotificationPreferenceViewSet(viewsets.ModelViewSet):
    queryset = PatientPortalNotificationPreference.objects.all()
    serializer_class = PatientPortalNotificationPreferenceSerializer


# ── Devices ─────────────────────────────────────────────────────────────
class PatientDeviceViewSet(viewsets.ModelViewSet):
    queryset = PatientDevice.objects.filter(revoked=False)
    serializer_class = PatientDeviceSerializer

    @action(detail=True, methods=["post"], url_path="revoke")
    def revoke(self, request, pk=None):
        device = self.get_object()
        device.revoked = True
        device.save(update_fields=["revoked", "updated_at"])
        return Response(status=status.HTTP_204_NO_CONTENT)


# ── NFC cards (patient / staff) ─────────────────────────────────────────
class NFCCardViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = NFCCard.objects.all()
    serializer_class = NFCCardSerializer

    def create(self, request):
        """Staff endpoint: issue a new card. Returns activation_code (shown once)."""
        s = NFCCardCreateSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        profile = PatientPortalProfile.objects.get(id=s.validated_data["profile_id"])
        activation_code = f"{secrets.randbelow(1_000_000):06d}"
        card = NFCCard.objects.create(
            profile=profile,
            public_key_pem=s.validated_data["public_key_pem"],
            chip_vendor=s.validated_data.get("chip_vendor", "desfire_ev3"),
            activation_code_hash=hashlib.sha256(activation_code.encode()).hexdigest(),
        )
        return Response(
            {"card": NFCCardSerializer(card).data, "activation_code": activation_code},
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"], url_path="activate")
    def activate(self, request, pk=None):
        card = self.get_object()
        code = request.data.get("activation_code", "")
        if hashlib.sha256(code.encode()).hexdigest() != card.activation_code_hash:
            return Response({"detail": "Invalid activation code"},
                            status=status.HTTP_400_BAD_REQUEST)
        card.activated_at = timezone.now()
        card.save(update_fields=["activated_at", "updated_at"])
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post"], url_path="revoke")
    def revoke(self, request, pk=None):
        card = self.get_object()
        card.revoked_at = timezone.now()
        card.revocation_reason = request.data.get("reason", "unspecified")
        card.save(update_fields=["revoked_at", "revocation_reason", "updated_at"])
        return Response(status=status.HTTP_204_NO_CONTENT)


class NFCScanLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = NFCScanLog.objects.all()
    serializer_class = NFCScanLogSerializer


# ── NFC public (called by provider terminals) ───────────────────────────
class NFCChallengeView(APIView):
    """Terminal calls this to get a fresh nonce before scanning."""
    permission_classes = [permissions.AllowAny]  # gated by terminal token in real deploy

    def post(self, request):
        card_uuid = request.data.get("card_uuid")
        if not card_uuid:
            return Response({"detail": "card_uuid required"}, status=400)
        return Response({"nonce": issue_challenge(card_uuid), "ttl": 60})


class NFCScanView(APIView):
    """Terminal calls this after reading the signed nonce off the card."""
    permission_classes = [permissions.AllowAny]  # gated by terminal token in real deploy

    def post(self, request):
        s = NFCScanPublicRequestSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        data = s.validated_data

        try:
            card = NFCCard.objects.select_related("profile__patient").get(
                card_uuid=data["card_uuid"]
            )
        except NFCCard.DoesNotExist:
            return Response({"detail": "Card not found"}, status=404)
        if not card.is_active:
            return Response({"detail": "Card is not active"}, status=401)

        if not verify_scan(card, data["nonce"], data["signature"]):
            return Response({"detail": "Invalid signature or expired nonce"}, status=401)

        summary = build_summary_for_purpose(card.profile, data["purpose"])

        # Log the scan (immutable audit)
        scan = NFCScanLog.objects.create(
            card=card,
            profile=card.profile,
            purpose=data["purpose"],
            terminal_id=data["terminal_id"],
            ip_address=request.META.get("REMOTE_ADDR"),
            scope_granted={"fields": list(summary.keys())},
        )
        # Emit patient-visible activity
        PatientPortalActivity.objects.create(
            profile=card.profile,
            activity_type="nfc_scan",
            description=f"{data['purpose']} scan by terminal {data['terminal_id']}",
            ip_address=request.META.get("REMOTE_ADDR"),
        )

        return Response({
            "patient_summary": summary,
            "scan_id": str(scan.id),
            "expires_in": 14400,   # 4 h scoped session (issue token in P0-3)
        })


# ── Emergency profile ─────────────────────────────────────────────────
class EmergencyProfileView(APIView):
    """GET/PATCH the emergency profile of the authenticated patient."""

    def _get_profile(self, request):
        return PatientPortalProfile.objects.get(user_id=request.user.id) \
            if request.user.is_authenticated else None

    def get(self, request):
        profile = self._get_profile(request)
        if not profile:
            return Response({"detail": "No patient profile"}, status=404)
        ep, _ = EmergencyProfile.objects.get_or_create(profile=profile)
        return Response(EmergencyProfileSerializer(ep).data)

    def patch(self, request):
        profile = self._get_profile(request)
        if not profile:
            return Response({"detail": "No patient profile"}, status=404)
        ep, _ = EmergencyProfile.objects.get_or_create(profile=profile)
        s = EmergencyProfileSerializer(ep, data=request.data, partial=True)
        s.is_valid(raise_exception=True)
        s.save()
        PatientPortalActivity.objects.create(
            profile=profile, activity_type="profile_updated",
            description="Emergency profile updated",
        )
        return Response(s.data)


# ── Delegation ───────────────────────────────────────────────────────
class DelegatedAccessViewSet(viewsets.ModelViewSet):
    queryset = DelegatedAccess.objects.all()
    serializer_class = DelegatedAccessSerializer

    @action(detail=True, methods=["post"], url_path="accept")
    def accept(self, request, pk=None):
        d = self.get_object()
        d.accepted_at = timezone.now()
        d.consent_signed_at = timezone.now()
        d.save(update_fields=["accepted_at", "consent_signed_at", "updated_at"])
        PatientPortalActivity.objects.create(
            profile=d.subject_profile, activity_type="delegated_grant",
            description=f"Granted to {d.delegate_profile_id} ({d.relationship})",
        )
        return Response({"status": "accepted"})

    @action(detail=True, methods=["post"], url_path="revoke")
    def revoke(self, request, pk=None):
        d = self.get_object()
        d.revoked_at = timezone.now()
        d.save(update_fields=["revoked_at", "updated_at"])
        PatientPortalActivity.objects.create(
            profile=d.subject_profile, activity_type="delegated_revoke",
            description=f"Revoked delegation to {d.delegate_profile_id}",
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


# ── Consent ──────────────────────────────────────────────────────────
class ConsentGrantViewSet(mixins.CreateModelMixin,
                          mixins.ListModelMixin,
                          mixins.RetrieveModelMixin,
                          viewsets.GenericViewSet):
    queryset = ConsentGrant.objects.all()
    serializer_class = ConsentGrantSerializer

    def destroy(self, request, *args, **kwargs):
        obj = self.get_object()
        obj.revoked_at = timezone.now()
        obj.save(update_fields=["revoked_at", "updated_at"])
        PatientPortalActivity.objects.create(
            profile=obj.profile, activity_type="consent_changed",
            description=f"Revoked consent for provider {obj.provider_tenant_id}",
        )
        return Response(status=status.HTTP_204_NO_CONTENT)
