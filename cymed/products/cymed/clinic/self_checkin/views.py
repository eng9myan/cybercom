from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from . import services
from .models import KioskSession
from rest_framework import serializers as drf_serializers


class KioskSessionSerializer(drf_serializers.ModelSerializer):
    class Meta:
        model = KioskSession
        fields = ["id", "kiosk_id", "appointment_id", "patient_profile_id",
                  "started_at", "completed_at", "stage", "identity_method",
                  "duration_seconds", "error_note"]
        read_only_fields = fields


class KioskSessionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = KioskSession.objects.all()
    serializer_class = KioskSessionSerializer

    @action(detail=False, methods=["post"], url_path="start")
    def start_(self, request):
        s = services.start(kiosk_id=request.data["kiosk_id"],
                            appointment_id=request.data.get("appointment_id"))
        return Response(KioskSessionSerializer(s).data, status=201)

    @action(detail=True, methods=["post"], url_path="identify")
    def identify(self, request, pk=None):
        s = services.identify(session_id=pk,
                                patient_profile_id=request.data["patient_profile_id"],
                                method=request.data["method"])
        return Response(KioskSessionSerializer(s).data)

    @action(detail=True, methods=["post"], url_path="verify-insurance")
    def verify(self, request, pk=None):
        s = services.verify_insurance(session_id=pk,
                                        policy_id=request.data["policy_id"],
                                        service_code=request.data["service_code"],
                                        provider_tenant_id=request.data["provider_tenant_id"])
        return Response(KioskSessionSerializer(s).data)

    @action(detail=True, methods=["post"], url_path="sign-consent")
    def consent(self, request, pk=None):
        s = services.sign_consent(session_id=pk)
        return Response(KioskSessionSerializer(s).data)

    @action(detail=True, methods=["post"], url_path="complete")
    def complete_(self, request, pk=None):
        s = services.complete(session_id=pk)
        return Response(KioskSessionSerializer(s).data)
