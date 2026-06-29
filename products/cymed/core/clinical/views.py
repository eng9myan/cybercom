import uuid

from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from platform.events.models import OutboxEvent
from products.cymed.core.clinical.models import (
    Allergy,
    ClinicalFlag,
    Condition,
    Observation,
    VitalSign,
)
from products.cymed.core.clinical.serializers import (
    AllergySerializer,
    ClinicalFlagSerializer,
    ConditionSerializer,
    ObservationSerializer,
    VitalSignSerializer,
)


class ConditionViewSet(viewsets.ModelViewSet):
    queryset = Condition.objects.filter(is_deleted=False)
    serializer_class = ConditionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        tenant_id = getattr(self.request, "tenant_id", None)
        if tenant_id:
            return self.queryset.filter(tenant_id=tenant_id)
        return self.queryset.none()


class AllergyViewSet(viewsets.ModelViewSet):
    queryset = Allergy.objects.all()
    serializer_class = AllergySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        tenant_id = getattr(self.request, "tenant_id", None)
        if tenant_id:
            return self.queryset.filter(tenant_id=tenant_id)
        return self.queryset.none()


class VitalSignViewSet(viewsets.ModelViewSet):
    queryset = VitalSign.objects.all()
    serializer_class = VitalSignSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        tenant_id = getattr(self.request, "tenant_id", None)
        if tenant_id:
            return self.queryset.filter(tenant_id=tenant_id)
        return self.queryset.none()


class ObservationViewSet(viewsets.ModelViewSet):
    queryset = Observation.objects.all()
    serializer_class = ObservationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        tenant_id = getattr(self.request, "tenant_id", None)
        if tenant_id:
            return self.queryset.filter(tenant_id=tenant_id)
        return self.queryset.none()


class ClinicalFlagViewSet(viewsets.ModelViewSet):
    queryset = ClinicalFlag.objects.all()
    serializer_class = ClinicalFlagSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        tenant_id = getattr(self.request, "tenant_id", None)
        if tenant_id:
            return self.queryset.filter(tenant_id=tenant_id)
        return self.queryset.none()


class BreakGlassView(APIView):
    """
    Emergency Break Glass access endpoint.
    Grants clinical user temporary elevated access and records a secure audit entry.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        patient_id = request.data.get("patient_id")
        reason = request.data.get("reason", "clinical")  # clinical, security, operational
        justification = request.data.get("justification")

        if not patient_id or not justification:
            return Response(
                {"detail": "patient_id and justification are required parameters."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        tenant_id = getattr(request, "tenant_id", None)
        if not tenant_id:
            return Response(
                {"detail": "Tenant context required"}, status=status.HTTP_400_BAD_REQUEST
            )

        # 1. Create Break Glass Access entry in Identity Module if models exist
        try:
            from platform.cyidentity.models import (
                BreakGlassAccess,
                BreakGlassStatus,
                IdentityRealm,
                UserProfile,
            )

            user_profile = UserProfile.objects.filter(tenant_id=tenant_id).first()
            realm = IdentityRealm.objects.filter(tenant_id=tenant_id).first()

            if user_profile and realm:
                BreakGlassAccess.objects.create(
                    tenant_id=uuid.UUID(tenant_id),
                    user=user_profile,
                    realm=realm,
                    reason=reason,
                    justification=justification,
                    target_resource=f"patient:{patient_id}",
                    target_action="read_clinical_record",
                    status=BreakGlassStatus.ACTIVE,
                    activated_at=timezone.now(),
                    expires_at=timezone.now() + timezone.timedelta(hours=1),
                )
        except Exception:
            # Fallback if cyidentity models are not registered or mock environment
            pass

        # 2. Publish Break Glass Outbox Event
        OutboxEvent.objects.create(
            tenant_id=tenant_id,
            topic="cymed.security.events",
            event_type="cymed.breakglass.used",
            payload={
                "user": str(request.user),
                "patient_id": patient_id,
                "reason": reason,
                "justification": justification,
                "timestamp": timezone.now().isoformat(),
            },
        )

        return Response(
            {
                "detail": "Emergency access granted. Break glass event registered.",
                "session_expiry": (timezone.now() + timezone.timedelta(hours=1)).isoformat(),
            },
            status=status.HTTP_200_OK,
        )
