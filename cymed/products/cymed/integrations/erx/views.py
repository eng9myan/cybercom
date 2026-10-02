"""
POST /api/v1/integrations/erx/transmit/            {prescription, network}
GET  /api/v1/integrations/erx/transmissions/        history (?prescription=)
POST /api/v1/integrations/erx/pdmp-checks/          {prescription}
POST /api/v1/integrations/erx/pdmp-checks/{id}/attest/
GET  /api/v1/integrations/erx/networks/             which networks are configured
"""
import os

from rest_framework import mixins, serializers, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response

from platform.api.permissions import IsAuthenticatedClinicalStaff, actor
from products.cymed.integrations.erx import services, transport
from products.cymed.integrations.erx.models import NETWORKS, ErxTransmission, PdmpCheck

PRESCRIBER_ROLES = {"physician", "doctor", "clinician", "consultant", "resident", "platform_admin", "tenant_admin"}


class ErxTransmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ErxTransmission
        fields = ["id", "prescription", "network", "status", "detail", "external_id",
                  "sent_by", "attempt", "created_at", "response"]
        read_only_fields = fields


class PdmpCheckSerializer(serializers.ModelSerializer):
    class Meta:
        model = PdmpCheck
        fields = ["id", "prescription", "patient_id", "result", "summary", "checked_by",
                  "reviewed_by", "reviewed_at", "created_at"]
        read_only_fields = fields


class _PrescriptionRef(serializers.Serializer):
    prescription = serializers.UUIDField()


class TransmitSerializer(_PrescriptionRef):
    network = serializers.ChoiceField(choices=[n for n, _ in NETWORKS])


def _prescription(request, rx_id):
    from products.cymed.pharmacy.prescriptions.models import Prescription

    return Prescription.objects.filter(id=rx_id, tenant_id=request.tenant_id).first()


def _not_found():
    return Response({"detail": "Prescription not found."}, status=status.HTTP_404_NOT_FOUND)


class ErxTransmissionViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = ErxTransmission.objects.all()
    serializer_class = ErxTransmissionSerializer
    permission_classes = [IsAuthenticatedClinicalStaff]
    filterset_fields = ["prescription", "network", "status"]


class PdmpCheckViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = PdmpCheck.objects.all()
    serializer_class = PdmpCheckSerializer
    permission_classes = [IsAuthenticatedClinicalStaff]
    filterset_fields = ["prescription", "result"]

    def create(self, request):
        ser = _PrescriptionRef(data=request.data)
        ser.is_valid(raise_exception=True)
        rx = _prescription(request, ser.validated_data["prescription"])
        if rx is None:
            return _not_found()
        check = services.run_pdmp_check(rx, checked_by=actor(request))
        return Response(PdmpCheckSerializer(check).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def attest(self, request, pk=None):
        from platform.api.permissions import _roles

        if not (_roles(request) & PRESCRIBER_ROLES):
            return Response({"detail": "Only a prescriber can attest PDMP review."},
                            status=status.HTTP_403_FORBIDDEN)
        check = services.attest_pdmp_review(self.get_object(), reviewer=actor(request))
        return Response(PdmpCheckSerializer(check).data)


@api_view(["POST"])
@permission_classes([IsAuthenticatedClinicalStaff])
def transmit(request):
    ser = TransmitSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    rx = _prescription(request, ser.validated_data["prescription"])
    if rx is None:
        return _not_found()
    tx = services.transmit(rx, network=ser.validated_data["network"], sent_by=actor(request))
    code = {"accepted": 201, "sent": 202, "blocked": 422, "rejected": 422,
            "not_configured": 503, "failed": 502}.get(tx.status, 200)
    return Response(ErxTransmissionSerializer(tx).data, status=code)


@api_view(["GET"])
@permission_classes([IsAuthenticatedClinicalStaff])
def networks(request):
    return Response([{"network": n, "name": label, "configured": transport.is_configured(n)}
                     for n, label in NETWORKS]
                    + [{"network": "pdmp", "name": "Prescription monitoring (PDMP)",
                        "configured": bool(os.environ.get("CYMED_PDMP_URL")),
                        "required": services.pdmp_required()}])
