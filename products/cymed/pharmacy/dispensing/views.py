"""
CyMed Pharmacy — Dispensing Views
"""
import uuid
import django.utils.timezone as tz
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status as http_status
from platform.events.models import OutboxEvent
from .models import (
    DispenseOrder, DispenseItem, DispenseBatch,
    DispenseVerification, DispenseAudit, DispenseStatus
)
from .serializers import (
    DispenseOrderSerializer, DispenseItemSerializer, DispenseBatchSerializer,
    DispenseVerificationSerializer, DispenseAuditSerializer
)
from ..views import PharmacyModelViewSet


class DispenseOrderViewSet(PharmacyModelViewSet):
    queryset = DispenseOrder.objects.prefetch_related(
        "items", "verifications", "audit_log"
    ).select_related()
    serializer_class = DispenseOrderSerializer
    required_feature = "pharmacy.dispensing"
    filterset_fields = ["dispense_type", "status", "pickup_method"]
    search_fields = ["dispense_number", "fhir_medication_dispense_id"]

    def perform_create(self, serializer):
        tenant_id = getattr(self.request, "tenant_id", None)
        dispense_number = f"DSP-{str(uuid.uuid4()).upper()[:12]}"
        obj = serializer.save(tenant_id=tenant_id, dispense_number=dispense_number)
        DispenseAudit.objects.create(
            tenant_id=tenant_id, dispense_order=obj,
            action="created",
            performed_by=self.request.user.id if hasattr(self.request, "user") else uuid.uuid4(),
            details={"dispense_number": obj.dispense_number},
        )

    @action(detail=True, methods=["post"], url_path="verify")
    def verify(self, request, pk=None):
        """Pharmacist verifies the dispense order before dispensing."""
        dispense = self.get_object()
        if dispense.status not in (DispenseStatus.VERIFICATION_PENDING, DispenseStatus.QUEUED):
            return Response(
                {"detail": "Order is not pending verification."},
                status=http_status.HTTP_400_BAD_REQUEST
            )
        pharmacist_id = request.user.id if hasattr(request, "user") else None
        dispense.status = DispenseStatus.VERIFIED
        dispense.verified_by = pharmacist_id
        dispense.verified_at = tz.now()
        dispense.save(update_fields=["status", "verified_by", "verified_at", "updated_at"])

        DispenseAudit.objects.create(
            tenant_id=dispense.tenant_id, dispense_order=dispense,
            action="verified", performed_by=pharmacist_id or uuid.uuid4(),
            details={"verified_at": str(dispense.verified_at)},
        )
        return Response(DispenseOrderSerializer(dispense).data)

    @action(detail=True, methods=["post"], url_path="dispense")
    def dispense(self, request, pk=None):
        """Mark order as dispensed to patient."""
        dispense = self.get_object()
        if dispense.status != DispenseStatus.VERIFIED:
            return Response(
                {"detail": "Order must be pharmacist-verified before dispensing."},
                status=http_status.HTTP_400_BAD_REQUEST
            )
        pharmacist_id = request.user.id if hasattr(request, "user") else None
        dispense.status = DispenseStatus.DISPENSED
        dispense.dispensed_by = pharmacist_id
        dispense.dispensed_at = tz.now()
        dispense.picked_up_by = request.data.get("picked_up_by", "")
        dispense.pickup_id_verified = request.data.get("pickup_id_verified", False)
        dispense.picked_up_at = tz.now()
        dispense.counseling_provided = request.data.get("counseling_provided", False)
        dispense.counseling_notes = request.data.get("counseling_notes", "")
        dispense.save()

        DispenseAudit.objects.create(
            tenant_id=dispense.tenant_id, dispense_order=dispense,
            action="dispensed", performed_by=pharmacist_id or uuid.uuid4(),
            details={"dispensed_at": str(dispense.dispensed_at), "picked_up_by": dispense.picked_up_by},
        )
        OutboxEvent.objects.create(
            tenant_id=str(dispense.tenant_id) if dispense.tenant_id else None,
            topic="cymed.pharmacy.dispense.completed",
            event_type="cymed.pharmacy.dispense.completed",
            payload={
                "dispense_id": str(dispense.id),
                "prescription_id": str(dispense.prescription_id) if dispense.prescription_id else None,
                "patient_id": str(dispense.patient_id),
            },
        )
        # Notify inventory bridge for consumption
        OutboxEvent.objects.create(
            tenant_id=str(dispense.tenant_id) if dispense.tenant_id else None,
            topic="cymed.inventory.consumed",
            event_type="cymed.inventory.consumed",
            payload={"dispense_id": str(dispense.id), "patient_id": str(dispense.patient_id)},
        )
        return Response(DispenseOrderSerializer(dispense).data)

    @action(detail=True, methods=["post"], url_path="barcode-verify")
    def barcode_verify(self, request, pk=None):
        """Verify medication via barcode scan."""
        dispense = self.get_object()
        item_id = request.data.get("item_id")
        ndc_scanned = request.data.get("ndc_code", "")
        try:
            item = dispense.items.get(id=item_id)
        except DispenseItem.DoesNotExist:
            return Response({"detail": "Item not found."}, status=http_status.HTTP_404_NOT_FOUND)

        if item.ndc_code and item.ndc_code != ndc_scanned:
            return Response(
                {"detail": "Barcode mismatch. Wrong medication.", "expected": item.ndc_code, "scanned": ndc_scanned},
                status=http_status.HTTP_400_BAD_REQUEST
            )
        pharmacist_id = request.user.id if hasattr(request, "user") else None
        item.barcode_verified = True
        item.barcode_verified_by = pharmacist_id
        item.barcode_verified_at = tz.now()
        item.status = "barcode_verified"
        item.save(update_fields=["barcode_verified", "barcode_verified_by", "barcode_verified_at", "status"])
        return Response({"verified": True, "item_id": str(item.id)})


class DispenseItemViewSet(PharmacyModelViewSet):
    queryset = DispenseItem.objects.select_related("dispense_order")
    serializer_class = DispenseItemSerializer
    required_feature = "pharmacy.dispensing"
    filterset_fields = ["dispense_order", "status", "barcode_verified"]


class DispenseBatchViewSet(PharmacyModelViewSet):
    queryset = DispenseBatch.objects.prefetch_related("dispense_orders")
    serializer_class = DispenseBatchSerializer
    required_feature = "pharmacy.dispensing"
    filterset_fields = ["batch_type", "status", "ward_id"]

    def perform_create(self, serializer):
        tenant_id = getattr(self.request, "tenant_id", None)
        batch_number = f"BATCH-{str(uuid.uuid4()).upper()[:10]}"
        serializer.save(tenant_id=tenant_id, batch_number=batch_number)

    @action(detail=True, methods=["post"], url_path="verify")
    def verify(self, request, pk=None):
        """Pharmacist verification of the full batch."""
        batch = self.get_object()
        pharmacist_id = request.user.id if hasattr(request, "user") else None
        batch.status = "verified"
        batch.verified_by = pharmacist_id
        batch.verified_at = tz.now()
        batch.save(update_fields=["status", "verified_by", "verified_at"])
        return Response(DispenseBatchSerializer(batch).data)


class DispenseVerificationViewSet(PharmacyModelViewSet):
    queryset = DispenseVerification.objects.select_related("dispense_order")
    serializer_class = DispenseVerificationSerializer
    required_feature = "pharmacy.dispensing"
    filterset_fields = ["verification_type", "result"]


class DispenseAuditViewSet(PharmacyModelViewSet):
    queryset = DispenseAudit.objects.select_related("dispense_order")
    serializer_class = DispenseAuditSerializer
    required_feature = "pharmacy.dispensing"
    filterset_fields = ["action", "is_override"]
    http_method_names = ["get", "head", "options"]   # Audit is read-only
