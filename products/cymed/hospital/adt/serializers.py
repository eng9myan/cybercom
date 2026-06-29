from rest_framework import serializers

from platform.events.models import OutboxEvent
from products.cymed.hospital.adt.models import (
    Admission,
    AdmissionReason,
    AdmissionType,
    DischargeDisposition,
    DischargeReason,
    DischargeSummary,
    TransferApproval,
    TransferRequest,
)


class AdmissionReasonSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdmissionReason
        fields = "__all__"


class AdmissionTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdmissionType
        fields = "__all__"


class DischargeReasonSerializer(serializers.ModelSerializer):
    class Meta:
        model = DischargeReason
        fields = "__all__"


class DischargeDispositionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DischargeDisposition
        fields = "__all__"


class AdmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Admission
        fields = [
            "id",
            "encounter",
            "admission_type",
            "admission_reason",
            "admitting_physician_id",
            "admitted_at",
            "status",
        ]
        read_only_fields = ["admitted_at"]

    def create(self, validated_data):
        tenant_id = validated_data.get("tenant_id")
        admission = super().create(validated_data)

        # Trigger Outbox Event
        OutboxEvent.objects.create(
            tenant_id=tenant_id,
            topic="cymed.hospital.events",
            event_type="cymed.hospital.admission.created",
            payload={
                "admission_id": str(admission.id),
                "encounter_id": str(admission.encounter.id),
                "patient_id": str(admission.encounter.patient.id),
                "admitted_at": admission.admitted_at.isoformat(),
                "status": admission.status,
            },
        )

        # Trigger ERP Billing Charge Event
        OutboxEvent.objects.create(
            tenant_id=tenant_id,
            topic="cymed.billing.events",
            event_type="cymed.charge.created",
            payload={
                "encounter_id": str(admission.encounter.id),
                "charge_type": "admission",
                "amount": 500.00,
                "currency": "AED",
                "service_code": "ADM-001",
            },
        )

        return admission


class TransferRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransferRequest
        fields = [
            "id",
            "patient",
            "encounter",
            "source_bed_id",
            "target_bed_id",
            "requested_by",
            "requested_at",
            "status",
            "reason",
        ]
        read_only_fields = ["requested_at"]


class TransferApprovalSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransferApproval
        fields = ["id", "transfer_request", "approved_by", "approved_at", "notes"]
        read_only_fields = ["approved_at"]

    def create(self, validated_data):
        tenant_id = validated_data.get("tenant_id")
        approval = super().create(validated_data)

        # Update Transfer Request status to Approved
        req = approval.transfer_request
        req.status = "approved"
        req.save()

        # Trigger Outbox Event for Transfer
        OutboxEvent.objects.create(
            tenant_id=tenant_id,
            topic="cymed.hospital.events",
            event_type="cymed.hospital.transfer.created",
            payload={
                "transfer_request_id": str(req.id),
                "patient_id": str(req.patient.id),
                "encounter_id": str(req.encounter.id),
                "source_bed_id": str(req.source_bed_id) if req.source_bed_id else None,
                "target_bed_id": str(req.target_bed_id),
                "approved_by": str(approval.approved_by),
                "timestamp": approval.approved_at.isoformat(),
            },
        )

        # Trigger ERP Billing Charge Event for Bed Transfer
        OutboxEvent.objects.create(
            tenant_id=tenant_id,
            topic="cymed.billing.events",
            event_type="cymed.charge.created",
            payload={
                "encounter_id": str(req.encounter.id),
                "charge_type": "bed_transfer",
                "amount": 150.00,
                "currency": "AED",
                "service_code": "TX-002",
            },
        )

        return approval


class DischargeSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = DischargeSummary
        fields = [
            "id",
            "admission",
            "discharged_at",
            "discharged_by",
            "disposition",
            "reason",
            "summary_text",
            "instructions",
        ]
        read_only_fields = ["discharged_at"]

    def create(self, validated_data):
        tenant_id = validated_data.get("tenant_id")
        summary = super().create(validated_data)

        # Update Admission status to discharged
        admission = summary.admission
        admission.status = "discharged"
        admission.save()

        # Trigger Outbox Event
        OutboxEvent.objects.create(
            tenant_id=tenant_id,
            topic="cymed.hospital.events",
            event_type="cymed.hospital.discharge.completed",
            payload={
                "admission_id": str(admission.id),
                "discharged_at": summary.discharged_at.isoformat(),
                "disposition_code": summary.disposition.code,
            },
        )

        return summary
