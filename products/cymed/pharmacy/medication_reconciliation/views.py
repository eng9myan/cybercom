"""CyMed Pharmacy — Medication Reconciliation Views."""

import django.utils.timezone as tz
from rest_framework.decorators import action
from rest_framework.response import Response

from platform.events.models import OutboxEvent

from ..views import PharmacyModelViewSet
from .models import (
    MedicationChange,
    MedicationConflict,
    MedicationReconciliation,
    ReconciliationStatus,
)
from .serializers import (
    MedicationChangeSerializer,
    MedicationConflictSerializer,
    MedicationReconciliationSerializer,
)


class MedicationReconciliationViewSet(PharmacyModelViewSet):
    queryset = MedicationReconciliation.objects.prefetch_related("medication_changes", "conflicts")
    serializer_class = MedicationReconciliationSerializer
    required_feature = "pharmacy.reconciliation"
    filterset_fields = ["reconciliation_type", "status", "patient_id", "encounter_id"]

    @action(detail=True, methods=["post"], url_path="complete")
    def complete(self, request, pk=None):
        """Complete reconciliation after all conflicts resolved."""
        rec = self.get_object()
        unresolved = rec.conflicts.filter(status="unresolved").count()
        if unresolved > 0:
            return Response(
                {
                    "detail": f"{unresolved} unresolved conflict(s) must be resolved before completion."
                },
                status=400,
            )
        rec.status = ReconciliationStatus.COMPLETED
        rec.completed_at = tz.now()
        rec.save(update_fields=["status", "completed_at", "updated_at"])

        OutboxEvent.objects.create(
            tenant_id=str(rec.tenant_id) if rec.tenant_id else None,
            topic="cymed.pharmacy.medication.reconciled",
            event_type="cymed.pharmacy.medication.reconciled",
            payload={
                "reconciliation_id": str(rec.id),
                "reconciliation_type": rec.reconciliation_type,
                "patient_id": str(rec.patient_id),
                "encounter_id": str(rec.encounter_id),
            },
        )
        return Response(MedicationReconciliationSerializer(rec).data)

    @action(detail=True, methods=["post"], url_path="compare-history")
    def compare_history(self, request, pk=None):
        """Compare reconciliation list with prescriptions/medication history."""
        rec = self.get_object()
        from products.cymed.pharmacy.prescriptions.models import MedicationHistory

        history = MedicationHistory.objects.filter(
            tenant_id=rec.tenant_id, patient_id=rec.patient_id, is_active=True
        ).values_list("drug_code", flat=True)
        current_codes = {m.get("drug_code") for m in rec.current_medications if isinstance(m, dict)}
        history_codes = set(history)
        missing_from_reconciliation = history_codes - current_codes
        return Response(
            {
                "history_medication_count": len(history_codes),
                "current_medication_count": len(current_codes),
                "possible_omissions": list(missing_from_reconciliation),
            }
        )


class MedicationChangeViewSet(PharmacyModelViewSet):
    queryset = MedicationChange.objects.select_related("reconciliation")
    serializer_class = MedicationChangeSerializer
    required_feature = "pharmacy.reconciliation"
    filterset_fields = ["change_type", "reconciliation"]


class MedicationConflictViewSet(PharmacyModelViewSet):
    queryset = MedicationConflict.objects.select_related("reconciliation")
    serializer_class = MedicationConflictSerializer
    required_feature = "pharmacy.reconciliation"
    filterset_fields = ["conflict_type", "status", "clinical_significance"]

    @action(detail=True, methods=["post"], url_path="resolve")
    def resolve(self, request, pk=None):
        """Resolve a medication conflict."""
        conflict = self.get_object()
        conflict.status = "resolved"
        conflict.resolved_by = request.user.id if hasattr(request, "user") else None
        conflict.resolution_notes = request.data.get("resolution_notes", "")
        conflict.resolved_at = tz.now()
        conflict.save(update_fields=["status", "resolved_by", "resolution_notes", "resolved_at"])
        return Response(MedicationConflictSerializer(conflict).data)
