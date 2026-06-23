"""
CyMed Pharmacy — Prescription Management Views
"""
import uuid
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from platform.events.models import OutboxEvent
from .models import (
    Prescription, PrescriptionItem, MedicationOrder,
    MedicationRenewal, MedicationRefill, PrescriptionAttachment,
    MedicationHistory, PrescriptionStatus, MedicationPriority
)
from .serializers import (
    PrescriptionSerializer, PrescriptionItemSerializer, MedicationOrderSerializer,
    MedicationRenewalSerializer, MedicationRefillSerializer,
    PrescriptionAttachmentSerializer, MedicationHistorySerializer
)
from ..views import PharmacyModelViewSet


class PrescriptionViewSet(PharmacyModelViewSet):
    queryset = Prescription.objects.prefetch_related(
        "items", "attachments", "renewals", "refills"
    ).select_related()
    serializer_class = PrescriptionSerializer
    required_feature = "pharmacy.prescriptions"
    filterset_fields = ["prescription_type", "status", "priority", "is_controlled"]
    search_fields = ["prescription_number", "fhir_medication_request_id"]

    def perform_create(self, serializer):
        tenant_id = getattr(self.request, "tenant_id", None)
        rx_number = f"RX-{str(uuid.uuid4()).upper()[:12]}"
        obj = serializer.save(tenant_id=tenant_id, prescription_number=rx_number)
        OutboxEvent.objects.create(
            tenant_id=str(tenant_id) if tenant_id else None,
            topic="cymed.pharmacy.prescription.created",
            event_type="cymed.pharmacy.prescription.created",
            payload={
                "prescription_id": str(obj.id),
                "prescription_number": obj.prescription_number,
                "patient_id": str(obj.patient_id),
                "type": obj.prescription_type,
                "is_controlled": obj.is_controlled,
            },
        )

    @action(detail=True, methods=["post"], url_path="verify")
    def verify(self, request, pk=None):
        """Pharmacist verification of prescription."""
        prescription = self.get_object()
        if prescription.status not in (PrescriptionStatus.PENDING, PrescriptionStatus.DRAFT):
            return Response(
                {"detail": "Prescription is not in a verifiable state."},
                status=status.HTTP_400_BAD_REQUEST
            )
        prescription.status = PrescriptionStatus.ACTIVE
        prescription.verified_by = request.user.id if hasattr(request, "user") else None
        import django.utils.timezone as tz
        prescription.verified_at = tz.now()
        prescription.save(update_fields=["status", "verified_by", "verified_at", "updated_at"])
        OutboxEvent.objects.create(
            tenant_id=str(prescription.tenant_id) if prescription.tenant_id else None,
            topic="cymed.pharmacy.prescription.verified",
            event_type="cymed.pharmacy.prescription.verified",
            payload={"prescription_id": str(prescription.id)},
        )
        return Response(PrescriptionSerializer(prescription).data)

    @action(detail=True, methods=["get"], url_path="medication-history")
    def medication_history(self, request, pk=None):
        """Patient's full medication history."""
        prescription = self.get_object()
        history = MedicationHistory.objects.filter(
            tenant_id=prescription.tenant_id,
            patient_id=prescription.patient_id
        ).order_by("-start_date")
        return Response(MedicationHistorySerializer(history, many=True).data)

    @action(detail=True, methods=["post"], url_path="cancel")
    def cancel(self, request, pk=None):
        """Cancel prescription."""
        prescription = self.get_object()
        reason = request.data.get("reason", "")
        prescription.status = PrescriptionStatus.CANCELLED
        prescription.save(update_fields=["status", "updated_at"])
        return Response({"status": "cancelled", "reason": reason})


class PrescriptionItemViewSet(PharmacyModelViewSet):
    queryset = PrescriptionItem.objects.select_related("prescription")
    serializer_class = PrescriptionItemSerializer
    required_feature = "pharmacy.prescriptions"
    filterset_fields = ["prescription", "is_active", "dispense_as_written"]


class MedicationOrderViewSet(PharmacyModelViewSet):
    queryset = MedicationOrder.objects.prefetch_related("status_history").select_related()
    serializer_class = MedicationOrderSerializer
    required_feature = "pharmacy.hospital"
    filterset_fields = ["order_type", "status", "priority", "is_controlled"]
    search_fields = ["order_number", "drug_name", "drug_code"]

    def perform_create(self, serializer):
        tenant_id = getattr(self.request, "tenant_id", None)
        order_number = f"MO-{str(uuid.uuid4()).upper()[:12]}"
        serializer.save(tenant_id=tenant_id, order_number=order_number)

    @action(detail=True, methods=["post"], url_path="verify")
    def verify(self, request, pk=None):
        """Pharmacist verification of medication order."""
        import django.utils.timezone as tz
        from .models import MedicationOrderStatus
        order = self.get_object()
        previous_status = order.status
        order.status = "verified"
        order.verified_by = request.user.id if hasattr(request, "user") else None
        order.verified_at = tz.now()
        order.save(update_fields=["status", "verified_by", "verified_at", "updated_at"])
        MedicationOrderStatus.objects.create(
            tenant_id=order.tenant_id,
            order=order, from_status=previous_status, to_status="verified",
            changed_by=order.verified_by,
        )
        OutboxEvent.objects.create(
            tenant_id=str(order.tenant_id) if order.tenant_id else None,
            topic="cymed.pharmacy.prescription.verified",
            event_type="cymed.pharmacy.prescription.verified",
            payload={"order_id": str(order.id), "order_number": order.order_number},
        )
        return Response(MedicationOrderSerializer(order).data)


class MedicationRenewalViewSet(PharmacyModelViewSet):
    queryset = MedicationRenewal.objects.select_related("prescription")
    serializer_class = MedicationRenewalSerializer
    required_feature = "pharmacy.prescriptions"
    filterset_fields = ["status"]


class MedicationRefillViewSet(PharmacyModelViewSet):
    queryset = MedicationRefill.objects.select_related("prescription")
    serializer_class = MedicationRefillSerializer
    required_feature = "pharmacy.prescriptions"
    filterset_fields = ["status", "pickup_method"]


class PrescriptionAttachmentViewSet(PharmacyModelViewSet):
    queryset = PrescriptionAttachment.objects.select_related("prescription")
    serializer_class = PrescriptionAttachmentSerializer
    required_feature = "pharmacy.prescriptions"
    filterset_fields = ["attachment_type"]


class MedicationHistoryViewSet(PharmacyModelViewSet):
    queryset = MedicationHistory.objects.all()
    serializer_class = MedicationHistorySerializer
    required_feature = "pharmacy.prescriptions"
    filterset_fields = ["patient_id", "is_active", "source"]
    search_fields = ["drug_name", "drug_code"]
